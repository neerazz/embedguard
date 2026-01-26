# EmbedGuard v3.0 - Zenodo Archive

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.14735192.svg)](https://doi.org/10.5281/zenodo.14735192)

## Cross-Layer Detection and Provenance Attestation for Adversarial Embedding Attacks in RAG Systems

**Author:** Neeraj Kumar Singh Beshane  
**ORCID:** [0009-0002-2125-1805](https://orcid.org/0009-0002-2125-1805)  
**IEEE Member ID:** 102037294  
**License:** MIT

---

## Quick Start (One-Line Reproducibility)

```bash
# Option 1: Docker (recommended)
docker run --rm ghcr.io/neerazz/embedguard:v1.0 python -m src.evaluation.run_benchmarks

# Option 2: Local installation
pip install -e . && python -m src.evaluation.run_benchmarks
```

All experiments use `seed=42` for deterministic reproduction.

---

## Contents

| Directory | Description |
|-----------|-------------|
| `src/` | EmbedGuard framework implementation |
| `data/` | Benchmark datasets and attack samples |
| `scripts/` | Evaluation and statistical test scripts |
| `tests/` | Unit and integration tests |
| `results/` | Pre-computed benchmark results |
| `paper/` | Manuscript, figures, and supplementary materials |
| `examples/` | Usage examples and tutorials |

---

## Benchmark Results (v3.0)

| Metric | Value | Notes |
|--------|-------|-------|
| Detection Rate | 100% (30/30) | Attacks detected |
| False Positive Rate | 0% (0/105) | Benign queries passed |
| Mean Latency | 0.04ms | AMD EPYC 7542 |
| P99 Latency | 0.14ms | Sub-millisecond |
| Jailbreak Deflection | 97.5% (117/120) | GCG, PAIR, AutoDAN, TAP |

**Statistical Significance:**
- Wilcoxon signed-rank test: p < 0.001
- Cohen's h effect size: 0.78 (large)
- 95% CI Detection Rate: [88.4%, 100%] (N=30)

---

## Attack Categories Covered (25 types)

1. Direct Instruction Injection
2. Jailbreak Attempts
3. Instruction Smuggling
4. Context Manipulation
5. Prompt Leaking
6. Role Manipulation
7. Indirect Injection
8. Unicode Obfuscation
9. Base64 Encoding
10. Delimiter Confusion
11. XML Injection
12. Markdown Injection
13. Developer Mode
14. Hypothetical Framing
15. Fictional Framing
16. Translation Attack
17. Repetition Attack
18. Authority Claim
19. Emotional Manipulation
20. RAG-Specific Attacks
21. Composite Attacks
22. Subtle Manipulation
23. Multi-Turn Setup
24. Payload Splitting
25. Virtualization

---

## Reproducing Paper Results

### Run Full Benchmark Suite
```bash
python -m src.evaluation.run_benchmarks
```

### Run Statistical Tests
```bash
python scripts/statistical_tests.py
```

### Run Unit Tests
```bash
pytest tests/ -v
```

### Generate Ablation Study
```bash
python -m src.evaluation.ablation_study
```

---

## File Manifest

```
embedguard-v3.0/
├── LICENSE                      # MIT License
├── README.md                    # Project documentation
├── CITATION.cff                 # Citation metadata
├── CHANGELOG.md                 # Version history
├── CONTRIBUTING.md              # Contribution guidelines
├── DATA_DESCRIPTION.md          # Dataset documentation
├── ZENODO_README.md             # This file
├── SUBMISSION_CHECKLIST.md      # Publication checklist
├── Dockerfile                   # Container for reproducibility
├── pyproject.toml               # Python package config
├── requirements.txt             # Dependencies
├── src/
│   ├── __init__.py
│   ├── core.py                  # Main EmbedGuard class
│   ├── config.py                # Configuration management
│   ├── types.py                 # Type definitions
│   ├── cli.py                   # Command-line interface
│   ├── prompt_detector/         # Layer 1: Prompt analysis
│   ├── embedding_attestation/   # Layer 2: TEE attestation
│   ├── retrieval_analyzer/      # Layer 3: Retrieval analysis
│   ├── output_verifier/         # Layer 4: Output verification
│   ├── correlation_engine/      # Cross-layer fusion
│   └── utils/                   # Utility functions
├── data/
│   ├── attacks/                 # Attack samples (35)
│   ├── benchmarks/              # Benchmark datasets
│   ├── samples/                 # Example queries
│   └── synthetic/               # Synthetic test data
├── scripts/
│   ├── run_benchmarks.py        # Benchmark runner
│   └── statistical_tests.py     # Statistical analysis
├── tests/
│   ├── test_core.py
│   ├── test_prompt_detector.py
│   ├── test_correlation_engine.py
│   └── test_neural_classifier.py
├── results/
│   ├── latest_results.json      # Latest benchmark run
│   └── statistical_analysis.json
├── paper/
│   ├── manuscript.md            # Full paper text
│   ├── figures/                 # Publication figures
│   └── appendix/                # Supplementary materials
└── examples/
    ├── quickstart.py
    ├── custom_patterns.py
    └── tee_integration.py
```

---

## Citation

```bibtex
@article{beshane2026embedguard,
  title={EmbedGuard: Cross-Layer Detection and Provenance Attestation for Adversarial Embedding Attacks in RAG Systems},
  author={Beshane, Neeraj Kumar Singh},
  journal={PeerJ Computer Science},
  year={2026},
  doi={10.5281/zenodo.14735192},
  url={https://github.com/neerazz/embedguard}
}
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v3.0 | 2026-01-24 | Added statistical tests, ablation study, adversarial stress-test |
| v2.1 | 2026-01-23 | Added failure mode analysis, enhanced ethics statement |
| v2.0 | 2026-01-22 | Cross-layer architecture, TEE attestation |
| v1.0 | 2026-01-20 | Initial release, pattern-based detection |

---

## Contact

- **Email:** neerazz@ieee.org
- **GitHub:** [@neerazz](https://github.com/neerazz)
- **ORCID:** [0009-0002-2125-1805](https://orcid.org/0009-0002-2125-1805)

---

## Acknowledgments

This work was conducted independently. The author thanks the open-source community for foundational tools and the reviewers for constructive feedback.

---

*Archived on Zenodo for FAIR-compliant long-term preservation.*
