# Paper

Source materials for the EmbedGuard paper.

## Contents

```
paper/
├── manuscript.md      # Full manuscript (Markdown) — v3.0, integrates both
│                      #   evaluation tiers and the 2025-2026 related work
├── images/            # Figures referenced by the manuscript
├── research/          # Supporting research artifacts
│   ├── novelty-scan-2026-07-09.md          # 32-paper annotated novelty scan
│   └── rag-security-evidence-2024-2026.md  # Verified CVE/OWASP/ATLAS/NIST evidence
└── scripts/
    ├── generate_figures.py        # Regenerates the figures
    └── generate_tier1_figures.py  # Higher-resolution variants
```

## Regenerating figures

```bash
pip install matplotlib numpy
python3 scripts/generate_figures.py
```

## Publication status

- Peer-reviewed: IJCESEN, 2026 — [DOI 10.22399/ijcesen.4869](https://doi.org/10.22399/ijcesen.4869)
- Code + data archive: [Zenodo 10.5281/zenodo.18364920](https://doi.org/10.5281/zenodo.18364920)

Title: EmbedGuard: Cross-Layer Detection and Provenance Attestation for
Adversarial Embedding Attacks in RAG Systems
Author: Neeraj Kumar Singh Beshane ([ORCID 0009-0002-2125-1805](https://orcid.org/0009-0002-2125-1805))
