# EmbedGuard Dataset Description

## Overview

This archive contains the EmbedGuard reference implementation, locally curated benchmark-style inputs, attack regression samples, and recorded result artifacts. The open benchmark exercises only the pattern-based prompt detector; it does not reproduce the archived production-scale, TEE, corpus-poisoning, or cross-layer results reported by the IJCESEN article.

## Repository Structure

```
embedguard/
├── embedguard/              # Python package
├── data/                    # Datasets
│   ├── benchmarks/          # Benign query datasets
│   └── attacks/             # Attack sample datasets
├── results/                 # Experimental results
├── examples/                # Usage examples
├── tests/                   # Test suite
└── paper/                   # Manuscript and figures
```

## Datasets

### Benchmark-Style Benign Queries

The repository labels these local files after Natural Questions, HotpotQA, and MS-MARCO, but does not include upstream example identifiers, extraction manifests, source revisions, or checksums. Treat them as curated benchmark-style regression inputs rather than verified subsets of the named upstream datasets.

| Dataset | Samples | Format | Description |
|---------|---------|--------|-------------|
| Natural Questions-style | 50 | JSONL | Locally curated factoid questions |
| HotpotQA-style | 25 | JSONL | Locally curated multi-hop questions |
| MS-MARCO-style | 25 | JSONL | Locally curated passage-retrieval queries |

**Total benign samples:** 100

### Attack Datasets

| Dataset | Samples | Format | Description |
|---------|---------|--------|-------------|
| Prompt Injection | 35 | JSONL | 30 attacks + 5 benign controls |
| Corpus Poisoning | 25 | JSONL | Prototype samples; not run by the Tier-2 benchmark |

The reproducible Tier-2 benchmark runs the 30 prompt attacks, the 5 prompt-file benign controls, and the 100 benchmark-style benign queries: 135 inputs total. It does not run the corpus-poisoning file.

## Data Formats

### Benchmark Question Format (JSONL)
```json
{
  "id": "nq_001",
  "question": "What is the capital of France?",
  "answer": "Paris",
  "context": "France is a country..."
}
```

### Attack Sample Format (JSONL)
```json
{
  "id": "inject_001",
  "attack_type": "direct_instruction",
  "payload": "Ignore all previous instructions...",
  "expected_detection": true,
  "expected_layer1_score": 0.95
}
```

## Experimental Results

The canonical v1.2 recorded run is `results/benchmark_results_20260710_025640.json`:

- **Included attacks detected:** 30/30
- **Included benign queries flagged:** 0/105
- **Detection-rate 95% Wilson interval:** 88.65%-100%
- **Specificity 95% Wilson interval:** 96.47%-100%

These are regression-set observations, not population estimates of production security. The JSON records SHA-256 hashes for every benchmark input and relevant source file, the nearest checked-out source commit when available, Python/platform/dependency versions, and timer characteristics. The file hashes bind the exact benchmark implementation even when Git metadata is absent, as in the Docker image. Latency remains a one-repetition, host- and load-dependent observation rather than a reproducible performance guarantee.

## Reproducibility

### Requirements
- Python 3.10+
- Project dependencies from `pyproject.toml`

### Running Benchmarks
```bash
./reproduce.sh
```

### Output
Results are saved to `results/` directory as:
- `benchmark_results_<timestamp>.json` - Machine-readable metrics
- `benchmark_report_*.md` - Human-readable report
- `statistical_analysis.json` - Wilson-interval summary derived from observed counts

## License

MIT License; see `LICENSE`.

## Citation

See CITATION.cff for citation information.

## Contact

For questions about this dataset, please open an issue on the GitHub repository.

---

Updated: 2026-07-10
