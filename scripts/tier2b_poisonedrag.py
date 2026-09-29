#!/usr/bin/env python3
"""Tier-2b open benchmark: PoisonedRAG (NQ) vs EmbedGuard provenance and retrieval layers.

Held-out protocol
-----------------
* Attack: PoisonedRAG released black-box adversarial texts
  (``results/adv_targeted_results/nq.json``, MIT). Each poison passage is
  ``question + "." + adv_text`` as in PoisonedRAG ``src/attack.py``; up to 5
  per target question are injected into the retrieval pool.
* Pool: BEIR-NQ passages that are qrels of every evaluated query, plus
  ``--distractors`` random corpus passages. This is a *subsample* of the
  2.68M-passage NQ corpus, which makes retrieval easier for the attacker's
  competitors than full-corpus retrieval; report it as such.
* Splits (seeded): the 100 PoisonedRAG targets are split 50 calibration /
  50 test; non-target NQ queries with qrels are split warm-up 150 /
  calibration 100 / test 200.
* One stateful ``RetrievalDistributionalAnalyzer`` streams warm-up clean
  queries, then the shuffled calibration mix, then the shuffled test mix.
* The L3 threshold is fitted with ``calibrate_threshold`` on calibration
  CLEAN scores only (target FPR 0.05, plus 0.01). All reported TPR/FPR/AUROC
  numbers come from the test split only.
* Provenance (L2) is reported under two threat models:
  ``oob``      - poison written into the store out-of-band, no certificate;
  ``pipeline`` - poison ingested through the approved pipeline, so it carries
                 a valid HMAC certificate (provenance cannot catch it).

* End to end: the public ``EmbedGuard`` API with distance-only retrieval
  weights, ``EmbedGuard.calibrate()`` on calibration CLEAN traffic, then the
  test stream; reported as the share of requests the guard FLAGs or BLOCKs.
* ``--poison-form stealth`` drops the verbatim question prefix from each
  poison passage (adversarial text only).

Usage::

    python scripts/tier2b_poisonedrag.py --data-dir /path/to/eg --distractors 5000 \\
        --poison-form blackbox

``--data-dir`` must contain ``prag_nq.json``, ``nq_corpus.parquet``,
``nq_queries.parquet`` and ``nq_qrels.tsv`` (HF ``BeIR/nq``); fetch them with
``scripts/fetch_tier2b_data.py``. Writes
``results/tier2b_poisonedrag_<form>_k<n>_<YYYYMMDD>.json`` and ``.md``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import platform
import random
import subprocess
import sys
import time
from importlib import metadata
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from loguru import logger  # noqa: E402

from embedguard.config import EmbedGuardConfig  # noqa: E402
from embedguard.core import EmbedGuard  # noqa: E402
from embedguard.embedding_attestation import EmbeddingAttestationLayer  # noqa: E402
from embedguard.retrieval_analyzer import RetrievalDistributionalAnalyzer  # noqa: E402
from embedguard.types import Document  # noqa: E402

INPUTS = ("prag_nq.json", "nq_corpus.parquet", "nq_queries.parquet", "nq_qrels.tsv")
MODEL = "sentence-transformers/all-mpnet-base-v2"
COMPONENTS = ("pca", "kl", "rank")


# --------------------------------------------------------------------- stats
def wilson(successes: int, n: int, z: float = 1.959964) -> Dict[str, Any]:
    """Point estimate with a 95% Wilson score interval."""
    if n == 0:
        return {"k": 0, "n": 0, "rate": None, "ci95": [None, None]}
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return {"k": successes, "n": n, "rate": p,
            "ci95": [max(0.0, centre - half), min(1.0, centre + half)]}


def auroc(pos: Sequence[float], neg: Sequence[float]) -> float | None:
    """Mann-Whitney AUROC (ties count one half)."""
    if not len(pos) or not len(neg):
        return None
    p, n = np.asarray(pos, float)[:, None], np.asarray(neg, float)[None, :]
    return float(((p > n).sum() + 0.5 * (p == n).sum()) / (p.size * n.size))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def version(pkg: str) -> str | None:
    if pkg == "embedguard":
        # Report the imported source, not possibly stale installed metadata.
        import embedguard
        return embedguard.__version__
    try:
        return metadata.version(pkg)
    except metadata.PackageNotFoundError:
        return None


def source_commit() -> Dict[str, Any]:
    def git(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=REPO, capture_output=True,
                              text=True, check=False).stdout.strip()
    return {"commit": git("rev-parse", "HEAD") or None,
            "dirty_files": [l for l in git("status", "--porcelain").splitlines() if l]}


# ---------------------------------------------------------------------- data
def load_inputs(data_dir: Path, n_distract: int, rng: random.Random,
                n_split: Dict[str, int], poison_form: str = "blackbox",
                poison_per_target: int = 5):
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    adv = json.loads((data_dir / "prag_nq.json").read_text())
    targets = sorted(adv)
    rng.shuffle(targets)
    half = len(targets) // 2
    target_split = {"calibration": targets[:half], "test": targets[half:]}

    qt = pq.read_table(data_dir / "nq_queries.parquet").to_pydict()
    queries = dict(zip(qt["_id"], qt["text"]))
    qrels: Dict[str, List[str]] = {}
    with open(data_dir / "nq_qrels.tsv") as f:
        next(f)
        for line in f:
            q, d, _ = line.rstrip("\n").split("\t")[:3]
            qrels.setdefault(q, []).append(d)
    others = sorted(q for q in queries if q not in adv and q in qrels)
    rng.shuffle(others)
    a, b, c = n_split["warmup"], n_split["calibration"], n_split["test"]
    if len(others) < a + b + c:
        raise SystemExit(f"need {a + b + c} clean queries, have {len(others)}")
    clean_split = {"warmup": others[:a], "calibration": others[a:a + b],
                   "test": others[a + b:a + b + c]}

    evaluated = targets + [q for ids in clean_split.values() for q in ids]
    need = sorted({d for q in evaluated for d in qrels.get(q, [])})
    ids_col = pq.read_table(data_dir / "nq_corpus.parquet", columns=["_id"])["_id"]
    distract = set(rng.sample(range(len(ids_col)), n_distract))
    mask = np.asarray(pc.is_in(ids_col, value_set=pa.array(need))
                      .to_numpy(zero_copy_only=False))
    keep = sorted(set(np.nonzero(mask)[0].tolist()) | distract)
    tbl = pq.read_table(data_dir / "nq_corpus.parquet").take(keep).to_pydict()
    clean_docs = [(i, f"{t}. {x}" if t else x)
                  for i, t, x in zip(tbl["_id"], tbl["title"], tbl["text"])]
    # blackbox: PoisonedRAG's black-box form (question prefix + adv text).
    # stealth: adv text only - removes the verbatim question prefix that makes
    # black-box poison trivially close to its target query.
    prefix = (lambda q: adv[q]["question"] + ".") if poison_form == "blackbox" else (lambda q: "")
    poison_docs = [(f"poison::{q}::{j}", prefix(q) + text)
                   for q in targets for j, text in enumerate(adv[q]["adv_texts"][:poison_per_target])]
    return (adv, queries, target_split, clean_split, clean_docs, poison_docs,
            len(ids_col))


# ------------------------------------------------------------------ pipeline
class _CachedEncoder:
    """Lets the real HMAC signer certify a precomputed vector."""

    def __init__(self) -> None:
        self.vector = None

    def encode(self, document, convert_to_numpy=True):  # noqa: D401
        return self.vector


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--distractors", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--target-fpr", type=float, default=0.05)
    ap.add_argument("--warmup", type=int, default=150)
    ap.add_argument("--calibration-clean", type=int, default=100)
    ap.add_argument("--test-clean", type=int, default=200)
    ap.add_argument("--out-dir", type=Path, default=REPO / "results")
    ap.add_argument("--poison-per-target", type=int, choices=range(1, 6), default=5,
                    help="adversarial passages injected per target question (PoisonedRAG uses 5)")
    ap.add_argument("--poison-form", choices=("blackbox", "stealth"), default="blackbox",
                    help="blackbox = question + '.' + adv_text (PoisonedRAG); stealth = adv_text only")
    args = ap.parse_args()
    logger.remove()

    t0 = time.time()
    rng = random.Random(args.seed)
    splits = {"warmup": args.warmup, "calibration": args.calibration_clean,
              "test": args.test_clean}
    (adv, queries, target_split, clean_split, clean_docs, poison_docs,
     corpus_size) = load_inputs(args.data_dir, args.distractors, rng, splits,
                                   args.poison_form, args.poison_per_target)
    print(f"pool clean={len(clean_docs)} poison={len(poison_docs)} "
          f"({time.time() - t0:.1f}s)", flush=True)

    import torch
    from sentence_transformers import SentenceTransformer

    device = "mps" if torch.backends.mps.is_available() else (
        "cuda" if torch.cuda.is_available() else "cpu")
    model = SentenceTransformer(MODEL, device=device)

    def enc(texts: List[str]) -> np.ndarray:
        return model.encode(texts, batch_size=64, convert_to_numpy=True,
                            normalize_embeddings=True, show_progress_bar=False)

    C = enc([d[1] for d in clean_docs])
    P = enc([d[1] for d in poison_docs])
    CP = np.vstack([C, P])
    print(f"embedded on {device} ({time.time() - t0:.1f}s)", flush=True)

    def retrieve(text: str, poisoned: bool) -> List[Tuple[str, str, np.ndarray, float]]:
        qv = enc([text])[0]
        E, docs = (CP, clean_docs + poison_docs) if poisoned else (C, clean_docs)
        sims = E @ qv
        top = np.argsort(-sims)[: args.top_k]
        return [(docs[i][0], docs[i][1], E[i], float(sims[i])) for i in top]

    attestor = EmbeddingAttestationLayer()
    cached = _CachedEncoder()
    attestor._embedding_model = cached
    certs: Dict[str, Any] = {}

    def to_docs(results, threat: str) -> List[Document]:
        out = []
        for did, text, vec, sim in results:
            if did not in certs:
                cached.vector = np.asarray(vec, dtype=np.float32)
                certs[did] = attestor.generate_embedding_with_attestation(text)
            emb, cert = certs[did]
            is_poison = did.startswith("poison::")
            out.append(Document(content=text, embedding=emb, document_id=did,
                                metadata={"similarity_score": sim},
                                attestation=None if (is_poison and threat == "oob") else cert))
        return out

    # Diagnostic analyzer: package-default weights, warmed up on clean traffic
    # only, then frozen so no calibration or test request (attacks included)
    # updates its baseline. It reports per-component scores for the AUROCs;
    # the rank component still reads rank history, which is order-dependent.
    analyzer = RetrievalDistributionalAnalyzer()
    for q in clean_split["warmup"]:
        analyzer.analyze(queries[q], to_docs(retrieve(queries[q], False), "pipeline"))
    analyzer.freeze_baseline()

    rows: List[Dict[str, Any]] = []
    for split in ("calibration", "test"):
        stream = [("clean", q) for q in clean_split[split]] + \
                 [("attack", q) for q in target_split[split]]
        rng.shuffle(stream)
        for kind, q in stream:
            text = queries[q] if kind == "clean" else adv[q]["question"]
            res = retrieve(text, poisoned=(kind == "attack"))
            docs_oob = to_docs(res, "oob")
            score, _, det = analyzer.analyze(text, docs_oob)
            p_oob = attestor.verify_batch(docs_oob)[2]
            p_pipe = attestor.verify_batch(to_docs(res, "pipeline"))[2]
            rows.append(dict(
                split=split, kind=kind, qid=q,
                n_poison_topk=sum(r[0].startswith("poison::") for r in res),
                l3_score=float(score),
                l3_components={k: (None if v is None else float(v))
                               for k, v in det["component_scores"].items()},
                rank_status=det["rank_correlation"].get("status"),
                prov_oob_flag=(p_oob["unverified"] + p_oob["failed"]) > 0,
                prov_pipeline_flag=(p_pipe["unverified"] + p_pipe["failed"]) > 0,
            ))

    cal_clean = [r["l3_score"] for r in rows if r["split"] == "calibration" and r["kind"] == "clean"]
    fprs = sorted({args.target_fpr, 0.01}, reverse=True)
    thresholds = {f"{f:g}": RetrievalDistributionalAnalyzer.calibrate_threshold(cal_clean, f)
                  for f in fprs}

    test = [r for r in rows if r["split"] == "test"]
    atk = [r for r in test if r["kind"] == "attack"]
    cln = [r for r in test if r["kind"] == "clean"]
    succ = [r for r in atk if r["n_poison_topk"] > 0]

    def comp(rs, name):
        return [r["l3_components"][name] or 0.0 for r in rs]

    l3: Dict[str, Any] = {}
    for f, thr in thresholds.items():
        l3[f"target_fpr_{f}"] = dict(
            threshold=thr,
            TPR_all_attacks=wilson(sum(r["l3_score"] > thr for r in atk), len(atk)),
            TPR_successful_attacks=wilson(sum(r["l3_score"] > thr for r in succ), len(succ)),
            FPR_clean=wilson(sum(r["l3_score"] > thr for r in cln), len(cln)),
        )
    l3["default_threshold_0.5"] = dict(
        TPR_all_attacks=wilson(sum(r["l3_score"] > 0.5 for r in atk), len(atk)),
        FPR_clean=wilson(sum(r["l3_score"] > 0.5 for r in cln), len(cln)))
    l3["AUROC"] = auroc([r["l3_score"] for r in atk], [r["l3_score"] for r in cln])
    l3["component_AUROC"] = {c: auroc(comp(atk, c), comp(cln, c)) for c in COMPONENTS}
    l3["rank_status_counts"] = {s: sum(r["rank_status"] == s for r in test)
                                for s in sorted({str(r["rank_status"]) for r in test})}

    # Calibrated profile: every choice below is fit on the CALIBRATION split
    # (50 attack targets + calibration-clean) and only then applied to TEST.
    cal = [r for r in rows if r["split"] == "calibration"]
    cal_atk = [r for r in cal if r["kind"] == "attack"]
    cal_cln = [r for r in cal if r["kind"] == "clean"]
    cal_auc = {c: auroc(comp(cal_atk, c), comp(cal_cln, c)) for c in COMPONENTS}
    # keep components that separate on calibration data; weight by margin over chance
    kept = {c: (a - 0.5) for c, a in cal_auc.items() if a is not None and a >= 0.6}

    def calibrated(r: Dict[str, Any]) -> float:
        total = sum(kept.values())
        return sum(w * (r["l3_components"][c] or 0.0) for c, w in kept.items()) / total if total else 0.0

    cal_clean_scores = [calibrated(r) for r in cal_cln]
    calibrated_profile = dict(
        method=("components kept iff calibration-split AUROC >= 0.6, weighted by (AUROC - 0.5); "
                "thresholds = quantile of calibration-clean scores; test split untouched"),
        calibration_component_AUROC=cal_auc,
        weights={c: w / sum(kept.values()) for c, w in kept.items()} if kept else {},
        AUROC=auroc([calibrated(r) for r in atk], [calibrated(r) for r in cln]),
    )
    for f in fprs:
        thr = RetrievalDistributionalAnalyzer.calibrate_threshold(cal_clean_scores, f)
        calibrated_profile[f"target_fpr_{f:g}"] = dict(
            threshold=thr,
            TPR_all_attacks=wilson(sum(calibrated(r) > thr for r in atk), len(atk)),
            FPR_clean=wilson(sum(calibrated(r) > thr for r in cln), len(cln)),
        )
    l3["calibrated_profile"] = calibrated_profile

    # End-to-end arm: the public EmbedGuard API a deployment would call.
    # Distance-only retrieval weights; EmbedGuard.calibrate() on clean
    # calibration traffic only (no attack sees calibration); then the test
    # stream. Only the retrieval layer runs: the queries are benign, so the
    # prompt layer has nothing to detect; there is no generator for the output
    # proxy; and provenance is reported separately above.
    e2e_rows: Dict[str, List[Dict[str, Any]]] = {}
    for f in fprs:
        guard = EmbedGuard(EmbedGuardConfig(
            enable_tee=False, enable_output_verification=False,
            enable_prompt_detection=False,
            retrieval_component_weights={"pca": 0.0, "kl": 1.0, "rank": 0.0}))
        for q in clean_split["warmup"]:
            guard.analyze(queries[q], to_docs(retrieve(queries[q], False), "pipeline"))
        cal_info = guard.calibrate(
            ((queries[q], to_docs(retrieve(queries[q], False), "pipeline"))
             for q in clean_split["calibration"]), target_fpr=f)
        stream = [("clean", q) for q in clean_split["test"]] + \
                 [("attack", q) for q in target_split["test"]]
        random.Random(args.seed + 1).shuffle(stream)
        out = []
        for kind, q in stream:
            text = queries[q] if kind == "clean" else adv[q]["question"]
            res = guard.analyze(text, to_docs(retrieve(text, kind == "attack"), "pipeline"))
            out.append(dict(kind=kind, qid=q, threat_score=float(res.threat_score),
                            decision=str(getattr(res.decision, "value", res.decision))))
        # Control: the same target questions retrieved from the CLEAN pool.
        # If these are flagged at the attack rate, the detector is reacting to
        # the questions, not to the poison.
        control = []
        for q in target_split["test"]:
            text = adv[q]["question"]
            res = guard.analyze(text, to_docs(retrieve(text, False), "pipeline"))
            control.append(dict(kind="target_question_clean_pool", qid=q,
                                threat_score=float(res.threat_score),
                                decision=str(getattr(res.decision, "value", res.decision))))
        e2e_rows[f"{f:g}"] = out + control
        flagged = lambda r: r["decision"] in ("flag", "block")  # noqa: E731
        ea = [r for r in out if r["kind"] == "attack"]
        ec = [r for r in out if r["kind"] == "clean"]
        l3.setdefault("end_to_end", {})[f"target_fpr_{f:g}"] = dict(
            calibration=cal_info,
            flagged_attacks=wilson(sum(map(flagged, ea)), len(ea)),
            flagged_clean=wilson(sum(map(flagged, ec)), len(ec)),
            flagged_target_questions_clean_pool=wilson(sum(map(flagged, control)), len(control)),
            AUROC=auroc([r["threat_score"] for r in ea], [r["threat_score"] for r in ec]),
        )

    summary = dict(
        benchmark="tier2b_poisonedrag",
        generated_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        scope=dict(
            dataset="BEIR-NQ subsample pool (qrels of evaluated queries + random distractors)",
            corpus_size_full=corpus_size, pool_clean=len(clean_docs),
            poison_passages=len(poison_docs), distractors=args.distractors,
            top_k=args.top_k, seed=args.seed, model=MODEL, device=device,
            attack=(f"PoisonedRAG released adv_texts (MIT), {args.poison_per_target} per target, "
                    f"form={args.poison_form}"),
            poison_per_target=args.poison_per_target, poison_form=args.poison_form,
            splits=dict(targets={k: len(v) for k, v in target_split.items()},
                        clean={k: len(v) for k, v in clean_split.items()}),
            calibration="threshold = quantile of calibration-split clean L3 scores only",
            input_sha256={n: sha256(args.data_dir / n) for n in INPUTS},
            versions={p: version(p) for p in ("embedguard", "numpy", "scipy", "torch",
                                              "sentence-transformers", "pyarrow")}
                     | {"python": platform.python_version()},
            source=source_commit(),
        ),
        test_split=dict(
            attack_retrieval_success=wilson(len(succ), len(atk)),
            mean_poison_in_topk=float(np.mean([r["n_poison_topk"] for r in atk])),
            l3=l3,
            provenance=dict(
                oob_no_certificate=dict(
                    detect_successful_attacks=wilson(sum(r["prov_oob_flag"] for r in succ), len(succ)),
                    FPR_clean=wilson(sum(r["prov_oob_flag"] for r in cln), len(cln))),
                pipeline_valid_hmac=dict(
                    detect_successful_attacks=wilson(sum(r["prov_pipeline_flag"] for r in succ), len(succ)),
                    FPR_clean=wilson(sum(r["prov_pipeline_flag"] for r in cln), len(cln))),
            ),
        ),
        runtime_s=round(time.time() - t0, 1),
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.out_dir / (f"tier2b_poisonedrag_{args.poison_form}_k{args.poison_per_target}"
                           f"_{dt.date.today():%Y%m%d}")
    stem.with_suffix(".json").write_text(json.dumps(
        dict(summary=summary, rows=rows, end_to_end_rows=e2e_rows), indent=1))
    stem.with_suffix(".md").write_text(render_md(summary))
    print(json.dumps(summary["test_split"], indent=1))
    print(f"wrote {stem}.json/.md ({summary['runtime_s']}s)")


def _fmt(w: Dict[str, Any]) -> str:
    if w["rate"] is None:
        return "n/a"
    lo, hi = w["ci95"]
    return f"{w['rate']:.3f} ({w['k']}/{w['n']}; 95% CI {lo:.3f}-{hi:.3f})"


def render_md(s: Dict[str, Any]) -> str:
    t, sc, l3 = s["test_split"], s["scope"], s["test_split"]["l3"]
    lines = [
        f"# Tier-2b: PoisonedRAG (NQ, {s['scope']['poison_form']}, {s['scope']['poison_per_target']}"
        " poison passages per target) vs EmbedGuard provenance and retrieval layers",
        "",
        f"Generated {s['generated_utc']} from commit `{sc['source']['commit']}`"
        f" (dirty files: {len(sc['source']['dirty_files'])}).",
        "",
        "## Scope",
        f"- Pool: {sc['pool_clean']} clean BEIR-NQ passages (subsample of {sc['corpus_size_full']};"
        f" {sc['distractors']} random distractors) + {sc['poison_passages']} poison passages",
        f"- Model: `{sc['model']}`, cosine, top-{sc['top_k']}; seed {sc['seed']}",
        f"- Splits: targets {sc['splits']['targets']}, clean {sc['splits']['clean']}",
        f"- {sc['calibration']}; all numbers below are TEST split only",
        "",
        "## Test split",
        "- Diagnostic analyzer: package-default weights, warmed up on 150 clean queries then frozen;"
        " used for per-component AUROCs and the default-threshold row",
        f"- Attack retrieval success (>=1 poison in top-k): {_fmt(t['attack_retrieval_success'])}",
        f"- L3 AUROC attack vs clean: {l3['AUROC']:.3f}",
        "- L3 component AUROC: " + ", ".join(
            f"{k}={v:.3f}" if v is not None else f"{k}=n/a"
            for k, v in l3["component_AUROC"].items()),
    ]
    for key, v in l3.items():
        if key.startswith("target_fpr_"):
            lines += [f"- L3 @ {key} (threshold {v['threshold']:.4f}): TPR {_fmt(v['TPR_all_attacks'])};"
                      f" FPR {_fmt(v['FPR_clean'])}"]
    d = l3["default_threshold_0.5"]
    lines += [f"- L3 @ default 0.5: TPR {_fmt(d['TPR_all_attacks'])}; FPR {_fmt(d['FPR_clean'])}"]
    cp = l3.get("calibrated_profile")
    if cp:
        lines += ["", "## L3 calibrated profile (fit on calibration split, scored on test)",
                  f"- Method: {cp['method']}",
                  "- Calibration-split component AUROC: " + ", ".join(
                      f"{k}={v:.3f}" if v is not None else f"{k}=n/a"
                      for k, v in cp["calibration_component_AUROC"].items()),
                  "- Weights: " + (", ".join(f"{k}={v:.3f}" for k, v in cp["weights"].items()) or "none"),
                  f"- Test AUROC: {cp['AUROC']:.3f}" if cp["AUROC"] is not None else "- Test AUROC: n/a"]
        for key, v in cp.items():
            if key.startswith("target_fpr_"):
                lines.append(f"- @ {key} (threshold {v['threshold']:.4f}): TPR {_fmt(v['TPR_all_attacks'])};"
                             f" FPR {_fmt(v['FPR_clean'])}")
    for key, v in l3.get("end_to_end", {}).items():
        if key == list(l3["end_to_end"])[0]:
            lines += ["", "## End to end: EmbedGuard.analyze() after EmbedGuard.calibrate() on clean traffic",
                      "- Config: retrieval layer only (prompt layer, HMAC simulator and output proxy off);"
                      " retrieval_component_weights pca=0, kl=1, rank=0; decision = FLAG or BLOCK"]
        c = v["calibration"]
        lines.append(f"- @ {key} (flag threshold {c['flag_threshold']:.4f}, {c['n_clean']} clean calibration"
                     f" requests): attacks flagged {_fmt(v['flagged_attacks'])}; clean flagged"
                     f" {_fmt(v['flagged_clean'])}; AUROC {v['AUROC']:.3f}")
        lines.append(f"  - control, same target questions against the clean pool: flagged"
                     f" {_fmt(v['flagged_target_questions_clean_pool'])}")
    lines += ["", "## Provenance (L2)"]
    for name, v in t["provenance"].items():
        lines.append(f"- {name}: detect {_fmt(v['detect_successful_attacks'])}; FPR {_fmt(v['FPR_clean'])}")
    lines += ["", "Input SHA-256:"] + [f"- `{k}`: `{v}`" for k, v in sc["input_sha256"].items()]
    lines += ["", "Versions: " + ", ".join(f"{k} {v}" for k, v in sc["versions"].items()), ""]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
