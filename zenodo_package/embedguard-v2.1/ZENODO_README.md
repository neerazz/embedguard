# EmbedGuard: Zenodo Archive

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)

## Artifact Description

This archive contains the complete research artifact for the paper:

**"EmbedGuard: Cross-Layer Security for Retrieval-Augmented Generation Systems"**

Submitted to PeerJ Computer Science, January 2026.

## Archive Contents

```
embedguard-v2.1/
├── README.md                    # Project documentation
├── ZENODO_README.md             # This file
├── LICENSE                      # MIT License
├── CITATION.cff                 # Citation metadata
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Project configuration
├── DATA_DESCRIPTION.md          # Dataset documentation
├── SUBMISSION_CHECKLIST.md      # Reproducibility checklist
│
├── src/                         # Source code
│   ├── __init__.py
│   ├── core.py                  # Core EmbedGuard framework
│   ├── config.py                # Configuration management
│   ├── types.py                 # Type definitions
│   ├── cli.py                   # Command-line interface
│   ├── prompt_detector/         # Prompt injection detection (81 patterns)
│   ├── embedding_attestation/   # TEE attestation module
│   ├── retrieval_analyzer/      # Retrieval anomaly detection
│   ├── correlation_engine/      # Threat score correlation
│   └── output_verifier/         # Output verification
│
├── data/                        # Benchmark datasets
│   ├── benchmarks/
│   │   ├── nq/questions.jsonl           # Natural Questions (50 samples)
│   │   ├── hotpotqa/questions.jsonl     # HotpotQA (25 samples)
│   │   └── msmarco/questions.jsonl      # MS-MARCO (25 samples)
│   └── attacks/
│       ├── injection/prompt_injection.jsonl  # 30 attacks, 25 categories
│       └── poison/corpus_poison.jsonl        # Corpus poisoning samples
│
├── results/                     # Benchmark results
│   ├── latest_results.json      # Primary results file
│   └── benchmark_report_*.md    # Human-readable reports
│
├── examples/                    # Usage examples
│   ├── basic_usage.py           # Basic API usage
│   ├── integration_example.py   # RAG integration
│   └── run_benchmarks.py        # Benchmark runner
│
├── tests/                       # Unit tests
│   ├── test_core.py
│   ├── test_prompt_detector.py
│   └── test_correlation_engine.py
│
└── paper/                       # Manuscript and figures
    ├── manuscript.md            # Main paper (Markdown)
    ├── EmbedGuard_PeerJ_Submission.docx  # Formatted submission
    └── figures/                 # All paper figures (PDF + PNG)
```

## Quick Start

### Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install EmbedGuard in development mode
pip install -e .
```

### Running Benchmarks

```bash
# Run full benchmark suite
python examples/run_benchmarks.py

# Results saved to results/latest_results.json
```

### Expected Results

The benchmark should produce:
- **Detection Rate**: 100% (30/30 attacks detected)
- **False Positive Rate**: 0% (100/100 benign correctly classified)
- **Mean Latency**: 0.04ms per query
- **Attack Categories**: 25 types, all detected at 100%

## Reproducibility

### System Requirements

- Python 3.10+
- No GPU required for benchmark execution
- ~100MB disk space
- Standard CPU (benchmarks complete in <1 second)

### Verification Steps

1. Clone/extract the archive
2. Install dependencies: `pip install -r requirements.txt`
3. Run benchmarks: `python examples/run_benchmarks.py`
4. Compare results with `results/latest_results.json`

### Random Seeds

All experiments use seed=42 for reproducibility.

## Benchmark Datasets

| Dataset | Samples | Purpose | Source |
|---------|---------|---------|--------|
| Natural Questions | 50 | QA benchmark | Kwiatkowski et al., 2019 |
| HotpotQA | 25 | Multi-hop reasoning | Yang et al., 2018 |
| MS-MARCO | 25 | Web search QA | Nguyen et al., 2016 |
| Injection Attacks | 30 | Security evaluation | Curated (25 categories) |
| Benign Control | 5 | Baseline verification | Mixed domains |

## Attack Categories

The injection dataset covers 25 attack types:
1. Direct instruction
2. Jailbreak attempts
3. Instruction smuggling
4. Context manipulation
5. Prompt leaking
6. Role manipulation
7. Indirect injection
8. Unicode obfuscation
9. Base64 encoding
10. Delimiter confusion
11. XML injection
12. Markdown injection
13. Developer mode
14. Hypothetical framing
15. Fictional framing
16. Translation attacks
17. Repetition attacks
18. Authority claims
19. Emotional manipulation
20. RAG-specific attacks
21. Composite attacks
22. Subtle manipulation
23. Multi-turn setup
24. Payload splitting
25. Virtualization attacks

## Citation

```bibtex
@article{gupta2026embedguard,
  title={EmbedGuard: Cross-Layer Security for Retrieval-Augmented Generation Systems},
  author={Gupta, Neeraj},
  journal={PeerJ Computer Science},
  year={2026},
  doi={10.5281/zenodo.XXXXXXX}
}
```

## License

MIT License - see LICENSE file for details.

## Contact

- Author: Neeraj Gupta
- Email: neeraj@parafin.com
- Repository: https://github.com/neerazz/embedguard

## Version History

- v2.1 (January 2026): Reconciled manuscript with actual benchmark results
- v2.0 (January 2026): Complete benchmark implementation
- v1.0 (January 2026): Initial release
