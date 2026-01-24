# EmbedGuard: Cross-Layer Detection and Provenance Attestation for Adversarial Embedding Attacks in RAG Systems

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Overview

EmbedGuard is a novel security framework that addresses adversarial embedding attacks in Retrieval-Augmented Generation (RAG) systems through cross-layer detection and hardware-backed cryptographic attestation. This repository contains the implementation and research artifacts for the paper submitted to PeerJ Computer Science.

**Author**: Neeraj Kumar Singh Beshane  
**Affiliation**: Independent Researcher, California, USA  
**Note**: This work was conducted independently and is not affiliated with Meta Platforms, Inc.

## Abstract

Embedding-based Retrieval-Augmented Generation (RAG) systems are critical infrastructure for production AI applications, yet they remain vulnerable to embedding space poisoning attacks that achieve disproportionate success with minimal payloads (1% corpus contamination, resulting in 80% attack success rates). Current single-layer defense approaches optimize for high-amplitude signals in narrow-dimensional subspaces, making them systematically vulnerable to coordinated cross-layer attacks that distribute adversarial signals across architectural layers.

EmbedGuard is an adaptive, cross-layer detection framework integrating hardware-backed cryptographic attestation with statistical anomaly detection across four RAG architectural layers:

1. **Prompt Layer**: Injection detection
2. **Embedding Layer**: Hardware attestation via Trusted Execution Environments (TEEs)
3. **Retrieval Layer**: Distributional analysis
4. **Output Layer**: Consistency verification

## Key Features

- **Cross-Layer Detection Architecture**: Unified security reasoning across four layers of the RAG architecture
- **Cryptographic Provenance Attestation**: Hardware-backed embedding generation using TEEs
- **Production-Scale Performance**: 94.7% detection rate with 51ms mean latency overhead
- **Adaptive Attack Resilience**: 89.3% detection rate against adaptive attacks
- **Flexible Deployment Modes**: Passive, gated, and active operational modes

## Performance Highlights

| Attack Type | Detection Rate | False Positive Rate | Mean Latency |
|-------------|----------------|---------------------|---------------|
| Optimization-Based | 94.7% | 3.2% | 47ms |
| Transferability-Based | 91.4% | 4.1% | 51ms |
| Semantic Manipulation | 88.9% | 3.8% | 49ms |
| Adaptive Attacks | 89.3% | 5.2% | 53ms |
| Coordinated Multi-Layer | 96.2% | 2.9% | 58ms |

## Key Contributions

1. **Cross-Layer Detection**: First framework to correlate anomaly signals across all RAG layers, providing 18.4 percentage point improvement over best single-layer approach

2. **Cryptographic Attestation**: Novel hardware-backed embedding generation that transforms security from statistical inference to cryptographic verification

3. **Production Evaluation**: Comprehensive evaluation on production-scale system (500,000 embeddings, 47,000 queries) with 27.9-35.1 percentage point improvements over existing defenses under adaptive attacks

4. **Deployment Framework**: Three operational modes enabling deployment across diverse organizational contexts and risk tolerances

## Architecture

EmbedGuard implements a multi-stage detection pipeline:

### Layer 1: Prompt Injection Detection
- DistilBERT-based neural classifier
- 87.3% detection accuracy with 4.2ms latency
- Trained on 156,000 adversarial-benign query pairs

### Layer 2: Cryptographic Embedding Attestation
- TEE-based embedding generation with hardware isolation
- Cryptographic signing of embedding provenance
- 1.8ms signature generation, 0.3ms validation overhead

### Layer 3: Retrieval Distributional Analysis
- Incremental PCA for similarity distribution monitoring
- Kullback-Leibler divergence metrics (15.2ms per query)
- Temporal rank correlation analysis

### Layer 4: Output Consistency Verification
- Perturbation-based stability testing
- 6.3ms latency for flagged queries
- Semantic similarity measurement across perturbed sets

## Repository Structure

```
embedguard/
├── README.md
├── LICENSE
├── .gitignore
├── paper/
│   └── EmbedGuard_Paper.pdf
├── src/
│   ├── prompt_detector/
│   ├── embedding_attestation/
│   ├── retrieval_analyzer/
│   ├── output_verifier/
│   └── correlation_engine/
├── experiments/
│   ├── evaluation_scripts/
│   └── results/
├── docs/
│   ├── setup.md
│   ├── usage.md
│   └── api_reference.md
└── examples/
    ├── basic_usage.py
    └── deployment_modes.py
```

## Installation

```bash
# Clone the repository
git clone https://github.com/neerazz/embedguard.git
cd embedguard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```python
from embedguard import EmbedGuardFramework

# Initialize framework
framework = EmbedGuardFramework(
    mode='active',  # Options: 'passive', 'gated', 'active'
    tee_enabled=True,
    detection_threshold=0.85
)

# Process query
query = "What are the latest AI security vulnerabilities?"
result = framework.process_query(query, corpus)

if result.threat_detected:
    print(f"Threat detected with confidence: {result.threat_score}")
    print(f"Affected layers: {result.affected_layers}")
else:
    print(f"Safe response: {result.response}")
```

## Deployment Modes

### Passive Mode
- All anomaly detections are logged without intervention
- Enables baseline understanding of threat landscape
- 2.3-4.7 MB per incident for forensic analysis

### Gated Mode
- High-confidence attacks (>0.70) flagged for manual review
- Comprehensive context and visualization tools
- 3-5 minutes average review time

### Active Mode
- Automatic blocking for threats >0.85
- Safe fallback responses or retrieval-free generation
- Production-ready with tunable thresholds

## Evaluation Results

### Comparative Performance

| Defense System | Baseline Detection | Adaptive Detection | Latency |
|----------------|--------------------|--------------------|----------|
| **EmbedGuard** | **94.7%** | **89.3%** | 51ms |
| RAGuard | 87.2% | 61.4% | 38ms |
| RobustRAG | 82.9% | 58.7% | 42ms |
| TrustRAG | 79.3% | 54.2% | 35ms |

### Ablation Study

| Configuration | Detection Rate | Δ from Full System |
|---------------|----------------|--------------------|
| Full System (4 Layers) | 94.7% | — |
| w/o Output Layer | 91.2% | -3.5pp |
| w/o Retrieval Layer | 87.4% | -7.3pp |
| w/o Embedding TEE | 84.6% | -10.1pp |
| w/o Prompt Layer | 89.8% | -4.9pp |
| Embedding Only (Best Single) | 76.3% | -18.4pp |

## Applications

EmbedGuard is designed for high-assurance applications where RAG system integrity is critical:

- **Healthcare**: Clinical decision support systems
- **Financial Services**: Trading systems and risk assessment
- **Legal Research**: Case law and regulatory compliance tools
- **Enterprise AI**: Knowledge management and retrieval systems

## Citation

If you use EmbedGuard in your research, please cite:

```bibtex
@article{beshane2024embedguard,
  title={EmbedGuard: Cross-Layer Detection and Provenance Attestation for Adversarial Embedding Attacks in RAG Systems},
  author={Beshane, Neeraj Kumar Singh},
  journal={PeerJ Computer Science},
  year={2024},
  note={Submitted}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security Considerations

- TEE implementation requires AMD SEV-SNP or Intel SGX hardware
- Production deployment should follow security best practices
- Regular updates recommended for detection model retraining
- Consult documentation for hardening guidelines

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests for:

- Bug fixes
- Performance improvements
- Additional attack vectors
- Documentation enhancements

## Contact

For questions, collaboration opportunities, or security concerns:

- **GitHub Issues**: [embedguard/issues](https://github.com/neerazz/embedguard/issues)
- **Email**: Available in paper publication

## Acknowledgments

This research was conducted independently. The author thanks the security research community for foundational work in adversarial ML and RAG system security.

## References

1. IBM Security, "Cost of a Data Breach Report 2024"
2. Zou et al., "PoisonedRAG: Knowledge Poisoning Attacks to RAG"
3. Liu et al., "Prompt Injection attack against LLM-integrated Applications"
4. Carlini et al., "Are aligned neural networks adversarially aligned?"

---

**Status**: Paper submitted to PeerJ Computer Science  
**Last Updated**: January 2026  
**Version**: 1.0.0
