# EmbedGuard Dataset Description

## Overview

This archive contains the EmbedGuard framework for protecting Retrieval-Augmented Generation (RAG) systems against embedding space poisoning attacks, including source code, benchmark datasets, attack samples, and experimental results.

## Repository Structure

```
embedguard/
├── src/                     # Source code
├── data/                    # Datasets
│   ├── benchmarks/          # Benign query datasets
│   └── attacks/             # Attack sample datasets
├── results/                 # Experimental results
├── examples/                # Usage examples
├── tests/                   # Test suite
└── paper/                   # Manuscript and figures
```

## Datasets

### Benchmark Datasets (Benign Queries)

| Dataset | Samples | Format | Description |
|---------|---------|--------|-------------|
| Natural Questions (NQ) | 50 | JSONL | Factoid Q&A pairs from Google |
| HotpotQA | 25 | JSONL | Multi-hop reasoning questions |
| MS-MARCO | 25 | JSONL | Passage retrieval queries |

**Total benign samples:** 100

### Attack Datasets

| Dataset | Samples | Format | Description |
|---------|---------|--------|-------------|
| Prompt Injection | 35 | JSONL | 30 attacks + 5 benign controls |
| Corpus Poisoning | 25 | JSONL | Embedding manipulation attacks |

**Total attack samples:** 60

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

Results from real execution of the benchmark runner:

- **Detection Rate (Recall):** 43.3% (pattern-based)
- **Precision:** 100.0%
- **False Positive Rate:** 0.0%
- **F1 Score:** 0.605
- **Mean Latency:** 0.02ms
- **P95 Latency:** 0.05ms

## Reproducibility

### Requirements
- Python 3.9+
- Dependencies: numpy, loguru, pydantic

### Running Benchmarks
```bash
cd embedguard
python3 -m venv .venv
source .venv/bin/activate
pip install numpy loguru pydantic
python examples/run_benchmarks.py --all
```

### Output
Results are saved to `results/` directory as:
- `latest_results.json` - Machine-readable metrics
- `benchmark_report_*.md` - Human-readable report

## License

Apache License 2.0

## Citation

See CITATION.cff for citation information.

## Contact

For questions about this dataset, please open an issue on the GitHub repository.

---

Generated: 2026-01-24
