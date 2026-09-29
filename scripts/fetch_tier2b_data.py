#!/usr/bin/env python3
"""Download and verify the inputs for scripts/tier2b_poisonedrag.py.

Every file is fetched from a pinned upstream revision and checked against a
SHA-256 recorded when the 2026-09-28 results were produced, so a rerun uses
byte-identical inputs or fails loudly.

Sources and licences:

* ``prag_nq.json`` - PoisonedRAG black-box adversarial texts for NQ,
  github.com/sleeepeer/PoisonedRAG (MIT), commit f660d72.
* ``nq_corpus.parquet`` / ``nq_queries.parquet`` - BEIR Natural Questions,
  huggingface.co/datasets/BeIR/nq (CC BY-SA 4.0), revision b7253e6. The
  corpus file is ~764 MB.
* ``nq_qrels.tsv`` - BEIR NQ test qrels, huggingface.co/datasets/BeIR/nq-qrels,
  revision 519acd4.

Usage::

    python scripts/fetch_tier2b_data.py --data-dir data/tier2b
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

INPUTS = {
    "prag_nq.json": (
        "https://raw.githubusercontent.com/sleeepeer/PoisonedRAG/"
        "f660d72174f06b13fae5163ce656e7b235db858f/results/adv_targeted_results/nq.json",
        "44df711454a9bada08e72e9e4a003a2cc845c43707ac93a3493e5168ec415cf2",
    ),
    "nq_queries.parquet": (
        "https://huggingface.co/datasets/BeIR/nq/resolve/"
        "b7253e6c379163d024ddb1d6948152a91a2e3b46/queries/queries-00000-of-00001.parquet",
        "c8f54a071a7e9efa95f65251e0a9e9f74ca232120b67d05dff6952900ebf51ce",
    ),
    "nq_qrels.tsv": (
        "https://huggingface.co/datasets/BeIR/nq-qrels/resolve/"
        "519acd4e48bb3e5da22b2b888ce36c614f4f2bc9/test.tsv",
        "6df0cd2cbbe88504b64c68f21e946a759b62c4d864225720cec256f0196e2210",
    ),
    "nq_corpus.parquet": (
        "https://huggingface.co/datasets/BeIR/nq/resolve/"
        "b7253e6c379163d024ddb1d6948152a91a2e3b46/corpus/corpus-00000-of-00001.parquet",
        "b7e8d5a99cfe94a1a0f175e274ae6d8f33fe0630f1ab529cd8537e82bd0aaa9e",
    ),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="Download and verify Tier-2b benchmark inputs.")
    ap.add_argument("--data-dir", type=Path, default=Path("data/tier2b"))
    args = ap.parse_args()
    args.data_dir.mkdir(parents=True, exist_ok=True)

    failed = []
    for name, (url, expected) in INPUTS.items():
        dest = args.data_dir / name
        if dest.exists() and sha256(dest) == expected:
            print(f"ok      {name} (cached)")
            continue
        print(f"fetch   {name}", flush=True)
        tmp = dest.with_suffix(dest.suffix + ".part")
        urllib.request.urlretrieve(url, tmp)
        got = sha256(tmp)
        if got != expected:
            tmp.unlink()
            failed.append(name)
            print(f"FAILED  {name}: sha256 {got} != {expected}", file=sys.stderr)
            continue
        tmp.replace(dest)
        print(f"ok      {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
