# EmbedGuard Paper - PeerJ Computer Science Submission

## Directory Structure

```
paper/
├── README.md                    # This file
├── manuscript.md                # Source manuscript (Markdown)
├── EmbedGuard_PeerJ_Submission.docx  # Submission-ready DOCX (with figures)
├── SUBMISSION_GUIDE.md          # PeerJ submission guidelines
├── PEERJ_ACCEPTANCE_PLAN.md     # PeerJ acceptance readiness plan
├── TIER1_VENUE_PLAN.md          # Future upgrade plan for Tier-1 venues
├── figures/                     # Publication figures
│   ├── figure1_architecture.png
│   ├── figure1_architecture.pdf
│   ├── figure2_tee_protocol.png
│   ├── figure2_tee_protocol.pdf
│   ├── figure3_comparative_detection.png
│   ├── figure3_comparative_detection.pdf
│   ├── figure4_ablation_study.png
│   ├── figure4_ablation_study.pdf
│   ├── figure5_latency_breakdown.png
│   └── figure5_latency_breakdown.pdf
└── scripts/
    ├── create_docx.py           # Generate DOCX from manuscript
    ├── generate_figures.py      # Generate paper figures
    └── generate_tier1_figures.py # Generate Tier-1 venue figures
```

## Quick Start

### Regenerate DOCX

```bash
cd paper/scripts
python3 -m venv .venv
source .venv/bin/activate
pip install python-docx
python3 create_docx.py
```

### Regenerate Figures

```bash
cd paper/scripts
python3 -m venv .venv
source .venv/bin/activate
pip install matplotlib numpy
python3 generate_figures.py
```

## Submission Status

| Item | Status |
|------|--------|
| Manuscript | ✅ Complete |
| Figures | ✅ Complete (5 figures) |
| DOCX with embedded figures | ✅ Complete (840 KB) |
| Ethics statement | ✅ Added |
| Statistical significance | ✅ Added |
| GitHub repository | ✅ https://github.com/neerazz/embedguard |
| Zenodo DOI | 🔲 Pending |

## Before Submission

1. Create Zenodo archive from GitHub release
2. Update DOI in manuscript.md (replace `XXXXXXX`)
3. Regenerate DOCX
4. Submit to PeerJ Computer Science

## Target Venues

- **Primary:** PeerJ Computer Science (current submission)
- **Future:** USENIX Security 2026 (see TIER1_VENUE_PLAN.md)

## Paper Details

- **Title:** EmbedGuard: Cross-Layer Detection and Provenance Attestation for Adversarial Embedding Attacks in RAG Systems
- **Author:** Neeraj Kumar Singh Beshane
- **Keywords:** RAG Security, Embedding Poisoning, TEE Attestation, Cross-Layer Detection
