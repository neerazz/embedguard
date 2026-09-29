# Tier-2b: open corpus-poisoning benchmark (PoisonedRAG)

The Tier-2 benchmark (`reproduce.sh`) tests the regex prompt detector. The attack EmbedGuard is designed against comes through the corpus instead: an attacker plants passages in the knowledge base, and an ordinary question retrieves them. Tier 2b tests that attack using published attack texts and a public corpus.

## Run it

```bash
pip install -e ".[neural]" pyarrow
python scripts/fetch_tier2b_data.py --data-dir data/tier2b   # ~765 MB, pinned revisions, SHA-256 checked
scripts/run_tier2b.sh data/tier2b                            # six configurations
```

Each configuration takes about a minute on an Apple M-series GPU and several minutes on a CPU. Every run writes `results/tier2b_poisonedrag_<form>_k<n>_<date>.json`, with per-query rows, and a `.md` summary. Both files record the input SHA-256 digests, library versions, device and source commit. The committed 2026-09-28 results were generated from a clean checkout of code commit `80873d7`, which contains every code change in the v1.3.0 release; the only uncommitted files each run lists are the result files written by the runs before it.

| Input | Source | Licence |
|---|---|---|
| `prag_nq.json` | [PoisonedRAG](https://github.com/sleeepeer/PoisonedRAG) `results/adv_targeted_results/nq.json`, commit `f660d72` | MIT |
| `nq_corpus.parquet`, `nq_queries.parquet` | [BeIR/nq](https://huggingface.co/datasets/BeIR/nq), revision `b7253e6` | CC BY-SA 4.0 |
| `nq_qrels.tsv` | [BeIR/nq-qrels](https://huggingface.co/datasets/BeIR/nq-qrels) `test.tsv`, revision `519acd4` | as upstream |

The data files are downloaded from their sources and are not redistributed here.

## Protocol

- **Retrieval.** `sentence-transformers/all-mpnet-base-v2`, normalised cosine similarity, top 5, seed 12. The pool has 5,658 clean passages: the relevance-judged passages for every evaluated query, plus 5,000 passages drawn at random from the 2,681,468-passage corpus.
- **Attack.** 1, 3 or 5 PoisonedRAG passages per target question (`--poison-per-target`), in one of two forms (`--poison-form`):
  - `blackbox` prepends the target question to each passage, as the released attack does.
  - `stealth` uses the passage alone.
- **Splits.** The 100 target questions are split 50 calibration / 50 test. Clean NQ queries are split 150 warm-up / 100 calibration / 200 test.
- **Detector.** The public API; no test example is used to fit anything:
  - Build the guard with only the retrieval layer enabled and `retrieval_component_weights={"pca": 0, "kl": 1, "rank": 0}`.
  - Warm up on the clean warm-up queries.
  - Run `EmbedGuard.calibrate()` on the clean calibration queries. This sets the flag threshold and freezes the baseline.
  - Run the test stream, with attacks and clean queries shuffled together.
  - A query counts as detected when the decision is FLAG or BLOCK.
- **Why distance only.** A selection rule applied to the calibration split keeps components whose calibration AUROC is at least 0.6; in all six configurations it keeps only the distance component. The rule uses the labels of the 50 calibration attacks, and both the distance-only setting and the 0.6 cut-off were chosen after a pilot on this dataset with the same split procedure, so the choice is not independent of this benchmark even though the test split played no part in it. With top-5 retrieval of 768-dimensional embeddings the distance runs on its diagonal path (a per-dimension scaled distance to the baseline mean).
- **Controls.**
  - The 200 held-out clean queries.
  - The 50 test target questions run against the unpoisoned pool. If these were flagged as often as the attacks, the detector would be reacting to the questions rather than to the poison.
- **Provenance** is scored under two threat models:
  - poison written into the store out of band, with no certificate;
  - poison submitted through the approved ingestion path, which issues it a valid HMAC certificate.

## Results (test split: 50 attacks, 200 clean queries per row)

| Form | Planted passages per target | Detected at 5% target FPR | Detected at 1% target FPR | AUROC |
|---|---|---|---|---|
| black-box | 5 | 50/50 (92.9–100%) | 50/50 (92.9–100%) | 1.000 |
| black-box | 3 | 43/50 (73.8–93.0%) | 18/50 (24.1–49.9%) | 0.985 |
| black-box | 1 | 7/50 (7.0–26.2%) | 0/50 (0.0–7.1%) | 0.669 |
| stealth | 5 | 48/50 (86.5–98.9%) | 35/50 (56.2–80.9%) | 0.996 |
| stealth | 3 | 33/50 (52.2–77.6%) | 11/50 (12.8–35.2%) | 0.961 |
| stealth | 1 | 7/50 (7.0–26.2%) | 0/50 (0.0–7.1%) | 0.658 |

Ranges are 95% Wilson intervals. In every row:

- **Clean queries flagged:** 6/200 at the 5% target and 1/200 at the 1% target.
- **Target questions against the unpoisoned pool flagged:** 3/50 and 0/50.
- **Retrieval:** poison reached the top 5 for all 50 test attacks.
- **Package defaults** (0.5/0.3/0.2 weights, uncalibrated 0.5 cut): 0/50 detected.
- **Provenance:** caught 50/50 passages written out of band, and 0/50 submitted through the approved pipeline.

## What this shows

1. **Provenance is necessary but not sufficient.** It catches vectors that bypass the approved ingestion path. It gives no signal for a poisoned document that goes through that path, and going through that path is how PoisonedRAG works.
2. **The retrieval layer catches concentrated poisoning, not a single planted passage.** The distance statistic measures how far the mean embedding of the retrieved set sits from the clean baseline. When 3 to 5 of the top 5 results are poisoned, that shift is large. When only one is, it is small. PoisonedRAG reports that attack success rises with the number of planted passages (its §5.3), so the blind spot is also where the attack is weakest. A one-passage attack that does succeed would still get through.
3. **The defaults do not work for this threat.** PCA reconstruction error and rank correlation carry no signal here (test AUROC 0.46–0.53 and 0.35–0.49 respectively, from a diagnostic analyzer frozen after warm-up), yet they hold 70% of the default weight. The defaults are kept for compatibility, so select the configuration above explicitly.

## What this does not show

- Full-corpus retrieval. The pool is 0.2% of NQ.
- An adaptive attacker who knows a distance detector is present and stays close to the clean distribution.
- Other datasets, embedding models or attack families.
- End-to-end attack success. The benchmark measures poisoned retrieval, not whether the LLM gave the attacker's answer.
- The four-layer fused decision. Only the retrieval layer runs in the end-to-end arm.
- The IJCESEN Tier-1 numbers, which this benchmark does not reproduce.
