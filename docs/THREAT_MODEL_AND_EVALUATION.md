# Threat Model and Evaluation Protocol

This document answers two questions that must stay separate:

1. Which attackers and attack paths is EmbedGuard designed to make observable?
2. Which parts of that design are supported by the archived article and by the open repository benchmark?

The short version: EmbedGuard models an attacker who can influence a query, a corpus document, or an untrusted embedding path. The open Tier-2 benchmark tests only a fixed lexical prompt detector. It does not evaluate corpus poisoning, retrieval steering, hardware attestation, the four-layer system, or the article's 94.7% result.

## Protected assets and trust boundaries

The protected assets are:

- source-document identity and integrity;
- the binding between a document, approved embedding model, and resulting vector;
- retrieval rank and similarity behavior;
- the evidence chain from retrieved sources to a generated answer;
- the enforcement decision and its audit record.

The design assumes that the verifier policy, approved-model policy, signing keys, and any hardware root of trust are administered separately from the attacker. A valid provenance record establishes how an artifact was produced; it does not establish that the source was truthful, authorized, or benign.

## Attacker profiles

### 1. External content submitter

**Access:** Can submit or influence content that a connector or application may ingest, such as an uploaded document, shared page, ticket, repository file, or workflow attachment. Has no signing key, verifier-policy access, or vector-store administration.

**Objective:** Cause a later benign query to retrieve attacker-controlled evidence and change the generated answer or downstream decision.

**Representative path:** Submit plausible-looking content containing indirect instructions or semantically optimized claims; wait for the content to be indexed and retrieved.

### 2. Query and retrieval-steering attacker

**Access:** Can send queries and observe responses or retrieval effects. May probe repeatedly but does not control the trusted ingestion service.

**Objective:** Steer retrieval toward attacker-preferred documents, discover decision thresholds, or combine a crafted query with previously poisoned content.

**Representative path:** Adapt query wording based on observed results until an attacker-selected source enters the top-ranked context.

### 3. Untrusted ingestion or vector-path attacker

**Access:** Can replace or introduce a document, model artifact, or vector outside the approved embedding path. Does not control the verifier or its trusted keys.

**Objective:** Break the document-model-vector lineage while presenting the artifact as legitimate.

**Representative path:** Insert a precomputed vector, modify a source after embedding, or use an unapproved model. A production hardware-backed design should reject or quarantine the artifact when its binding, signature, measurement, or freshness check fails. The released package simulates this binding with HMAC and does not provide a hardware trust boundary.

### 4. Adaptive multi-surface attacker

**Access:** Combines the capabilities above and probes thresholds over time. Can keep each individual signal weak, but cannot compromise every trusted root by assumption.

**Objective:** Evade lexical, provenance, retrieval, and output checks simultaneously or poison the statistical baseline gradually.

**Representative path:** Use fluent content with no obvious injection phrase, valid-looking metadata, low-amplitude retrieval steering, and repeated probes intended to learn thresholds.

## Explicit exclusions

EmbedGuard does not claim to solve:

- complete compromise of verifier policy, signing keys, or the hardware root of trust;
- a malicious authorized administrator who can change both the source and its approval policy;
- compromised foundation-model weights or unsafe downstream tool permissions;
- authorization mistakes, source-admission mistakes, or semantic truth;
- physical or silicon-level attacks;
- attacks that evade every observed signal while preserving valid provenance.

These exclusions are why the recommended deployment path is passive observation, then gated review, then narrowly calibrated blocking—not automatic trust in a single score.

## Scenario construction

The architecture is best evaluated with scenarios tied to the attacker profiles above:

| Scenario | Attacker-controlled input | Trigger | Security question | Primary signal |
|---|---|---|---|---|
| Indirect prompt injection | Instructions inside retrieved content | Benign query retrieves the content | Does the retrieved text contain manipulation instructions? | Prompt/content detector, if the integration scans retrieved text |
| Corpus poisoning | Plausible document inserted through a connector or upload | Later query ranks it into context | Did the source enter through an approved path, and does retrieval behavior deviate? | Provenance plus retrieval analysis |
| Retrieval steering | Query or document optimized for target similarity/rank | Targeted retrieval request | Is ranking or embedding behavior inconsistent with the established corpus? | Retrieval analysis |
| Vector/provenance tampering | Document, model, vector, or metadata changed outside the approved path | Verification before retrieval | Did approved code and model create this vector from this document? | Provenance verification |
| Adaptive low-signal attack | Weak evidence distributed across surfaces | Repeated probing or delayed activation | Do several independent observations form one coherent attack path? | Correlation engine plus operational controls |

The repository includes prototype corpus-poisoning samples under `data/attacks/poison/`, but the open Tier-2 benchmark does not execute them. Their presence is not evaluation evidence.

## Evaluation tiers

### Tier 1: archived version-of-record claims

The IJCESEN article reports a four-layer evaluation at 500,000 embeddings and 47,000 queries, including 94.7% detection for optimization attacks, 89.3% for adaptive attacks, a 3.2% headline false-positive rate, and 51 ms mean overhead.

The repository does not contain the production corpus, raw predictions, attack generator, baseline configurations, threshold-calibration records, hardware-attestation logs, or per-example outputs needed to audit those claims. It therefore does not contain enough evidence to reconstruct a Tier-1 train/test split or the exact conditions behind the 94.7% result beyond the protocol description preserved in the article and `paper/manuscript.md`.

Treat Tier 1 as an immutable published record, not as a result reproduced by this repository.

### Tier 2: open fixed-file regression benchmark

Tier 2 runs the released `PromptInjectionDetector` in pattern-only mode:

- 83 fixed regex signatures;
- threshold `0.70`;
- neural path disabled;
- 30 attack strings plus 5 benign controls from `data/attacks/injection/prompt_injection.jsonl`;
- 100 locally curated benign strings: 50 Natural Questions-style, 25 HotpotQA-style, and 25 MS-MARCO-style;
- 135 rows total.

The named benign files do not carry upstream row IDs, extraction manifests, source revisions, or checksums. They are local regression inputs, not verified subsets of the public datasets whose names they reference.

For each row, the runner calls the detector once, records the score and matched patterns, and classifies a row as detected when `score > 0.70`. It then derives the confusion matrix, per-category counts, and one wall-clock timing sample per row. `scripts/statistical_tests.py` computes two-sided 95% Wilson intervals from the observed attack and benign counts.

The canonical recorded v1.2.0 run is `results/benchmark_results_20260710_025640.json`. It binds the exact input and source files by SHA-256 and records the source commit, Python/platform/dependency versions, timer implementation, and one-repetition timing scope.

## Why there is no train/test split in Tier 2

Tier 2 does not train or fit a classifier. It executes a hand-authored, fixed lexical pattern set against a fixed regression corpus. There is therefore no model-training set and no train/test split to report.

That does **not** make the 135 rows an independent generalization test. The patterns and samples are curated and may reflect overlapping attack concepts. The result supports only this bounded statement: the released detector found 30/30 included attacks and flagged 0/105 included benign strings in the committed run. It does not establish performance on unseen attacks, production traffic, multilingual inputs, indirect corpus attacks, or adaptive adversaries.

A future generalization study should freeze detector rules before evaluation, use a separately sourced and held-out attack corpus, add hard benign negatives, preserve upstream provenance, and preregister thresholds and exclusions.

## Reproduction procedure

```bash
./reproduce.sh
```

The script:

1. creates or reuses a Python 3.10+ virtual environment;
2. installs the package and development dependencies;
3. runs the unit tests;
4. runs the four Tier-2 input files through `examples/run_benchmarks.py`;
5. derives count-based uncertainty with `scripts/statistical_tests.py`.

Expected classification counts for the committed inputs are 30 true positives, 0 false negatives, 105 true negatives, and 0 false positives. Latency values are host- and load-dependent and should not be treated as a service-level performance claim.

## What each result can support

| Claim | Tier 1 | Tier 2 |
|---|---:|---:|
| Archived full-system rates and ablation | Reported in article | No |
| Reproducible pattern-detector behavior on committed strings | No | Yes |
| Corpus-poisoning detection | Reported scope only; raw evidence unavailable | No |
| Cross-layer benefit | Archived ablation only; not independently auditable here | No |
| Hardware-attestation behavior | Reported design/environment only; logs unavailable | No |
| Generalization to unseen or production traffic | No | No |
| One-command inspectable benchmark | No | Yes |

## Files that define the open experiment

- `DATA_DESCRIPTION.md` — row counts, formats, and provenance limits
- `data/attacks/injection/prompt_injection.jsonl` — 30 attacks and 5 benign controls
- `data/benchmarks/*/questions.jsonl` — 100 local benign strings
- `embedguard/prompt_detector/__init__.py` — released detector and fixed signatures
- `examples/run_benchmarks.py` — execution and metric collection
- `scripts/statistical_tests.py` — Wilson intervals from observed counts
- `results/benchmark_results_20260710_025640.json` — canonical machine-readable run
- `paper/manuscript.md` §4 — archived Tier-1 record and Tier-2 analysis
