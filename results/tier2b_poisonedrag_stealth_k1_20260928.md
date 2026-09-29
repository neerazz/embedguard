# Tier-2b: PoisonedRAG (NQ, stealth, 1 poison passages per target) vs EmbedGuard provenance and retrieval layers

Generated 2026-09-29T06:10:41+00:00 from commit `80873d70259594a1a6e3ee10cfe41cc72166a1ce` (dirty files: 10).

## Scope
- Pool: 5658 clean BEIR-NQ passages (subsample of 2681468; 5000 random distractors) + 100 poison passages
- Model: `sentence-transformers/all-mpnet-base-v2`, cosine, top-5; seed 12
- Splits: targets {'calibration': 50, 'test': 50}, clean {'warmup': 150, 'calibration': 100, 'test': 200}
- threshold = quantile of calibration-split clean L3 scores only; all numbers below are TEST split only

## Test split
- Diagnostic analyzer: package-default weights, warmed up on 150 clean queries then frozen; used for per-component AUROCs and the default-threshold row
- Attack retrieval success (>=1 poison in top-k): 1.000 (50/50; 95% CI 0.929-1.000)
- L3 AUROC attack vs clean: 0.615
- L3 component AUROC: pca=0.489, kl=0.674, rank=0.490
- L3 @ target_fpr_0.05 (threshold 0.4063): TPR 0.100 (5/50; 95% CI 0.043-0.214); FPR 0.065 (13/200; 95% CI 0.038-0.108)
- L3 @ target_fpr_0.01 (threshold 0.4164): TPR 0.060 (3/50; 95% CI 0.021-0.162); FPR 0.035 (7/200; 95% CI 0.017-0.070)
- L3 @ default 0.5: TPR 0.000 (0/50; 95% CI 0.000-0.071); FPR 0.000 (0/200; 95% CI 0.000-0.019)

## L3 calibrated profile (fit on calibration split, scored on test)
- Method: components kept iff calibration-split AUROC >= 0.6, weighted by (AUROC - 0.5); thresholds = quantile of calibration-clean scores; test split untouched
- Calibration-split component AUROC: pca=0.502, kl=0.765, rank=0.462
- Weights: kl=1.000
- Test AUROC: 0.674
- @ target_fpr_0.05 (threshold 0.5072): TPR 0.140 (7/50; 95% CI 0.070-0.262); FPR 0.025 (5/200; 95% CI 0.011-0.057)
- @ target_fpr_0.01 (threshold 0.5554): TPR 0.000 (0/50; 95% CI 0.000-0.071); FPR 0.000 (0/200; 95% CI 0.000-0.019)

## End to end: EmbedGuard.analyze() after EmbedGuard.calibrate() on clean traffic
- Config: retrieval layer only (prompt layer, HMAC simulator and output proxy off); retrieval_component_weights pca=0, kl=1, rank=0; decision = FLAG or BLOCK
- @ target_fpr_0.05 (flag threshold 0.4995, 100 clean calibration requests): attacks flagged 0.140 (7/50; 95% CI 0.070-0.262); clean flagged 0.030 (6/200; 95% CI 0.014-0.064); AUROC 0.658
  - control, same target questions against the clean pool: flagged 0.060 (3/50; 95% CI 0.021-0.162)
- @ target_fpr_0.01 (flag threshold 0.5457, 100 clean calibration requests): attacks flagged 0.000 (0/50; 95% CI 0.000-0.071); clean flagged 0.005 (1/200; 95% CI 0.001-0.028); AUROC 0.658
  - control, same target questions against the clean pool: flagged 0.000 (0/50; 95% CI 0.000-0.071)

## Provenance (L2)
- oob_no_certificate: detect 1.000 (50/50; 95% CI 0.929-1.000); FPR 0.000 (0/200; 95% CI 0.000-0.019)
- pipeline_valid_hmac: detect 0.000 (0/50; 95% CI 0.000-0.071); FPR 0.000 (0/200; 95% CI 0.000-0.019)

Input SHA-256:
- `prag_nq.json`: `44df711454a9bada08e72e9e4a003a2cc845c43707ac93a3493e5168ec415cf2`
- `nq_corpus.parquet`: `b7e8d5a99cfe94a1a0f175e274ae6d8f33fe0630f1ab529cd8537e82bd0aaa9e`
- `nq_queries.parquet`: `c8f54a071a7e9efa95f65251e0a9e9f74ca232120b67d05dff6952900ebf51ce`
- `nq_qrels.tsv`: `6df0cd2cbbe88504b64c68f21e946a759b62c4d864225720cec256f0196e2210`

Versions: embedguard 1.3.0, numpy 2.5.3, scipy 1.18.1, torch 2.14.0, sentence-transformers 6.1.0, pyarrow 25.0.1, python 3.12.14
