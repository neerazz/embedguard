# Changelog

All notable changes to EmbedGuard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-07-09

Post-publication maintenance and manuscript extension. The paper's published
results (IJCESEN, DOI 10.22399/ijcesen.4869) are unchanged — this release
updates the repository and manuscript around them. Tagged explicitly so the
delta from the version of record is auditable, not silent drift.

### Fixed

- **Correlation engine scoring**: replaced the mis-calibrated log-odds update
  with weighted consensus plus a strongest-signal floor (fail-closed). A
  high-confidence single-layer detection is no longer diluted by quiet
  layers; decisions now match the documented flag/block thresholds.
- **Whitespace-evasion detection**: normalized-text pattern variants with
  optional whitespace so obfuscated attacks ("I g n o r e ...") are caught;
  backreference patterns excluded to avoid catastrophic regex backtracking.
- Placeholder author emails; stale PeerJ submission-status references;
  CITATION.cff now cites the published IJCESEN article.

### Changed

- **Manuscript v3.0** (`paper/manuscript.md`):
  - Results restructured into two explicit evaluation tiers: Tier 1
    (production-scale reference results from the version of record) and
    Tier 2 (open 135-sample benchmark, reproducible via `reproduce.sh`),
    with a section reconciling why the tiers differ.
  - Novelty claims scoped against a 32-paper 2024-2026 literature scan
    (`paper/research/novelty-scan-2026-07-09.md`): "first" claims narrowed
    to four-layer signal *fusion* and *hardware-rooted* embedding
    provenance; concurrent layered/provenance work cited and contrasted
    (new Section 2.4, new Limitation 8).
  - Introduction grounded in verified production threat evidence
    (CVE-2025-32711/EchoLeak, ConfusedPilot, Phantom, OWASP LLM01/04/08
    2025, MITRE ATLAS AML.T0064/66/70/71, NIST AI 100-2e2025; sources in
    `paper/research/rag-security-evidence-2024-2026.md`).
  - References expanded to 39 entries, all verified; figures embedded.
- README contribution claims aligned with the scoped wording.

### Removed

- Repository bloat: `zenodo_package/` duplicates and archives, duplicate
  `src/` tree, submission zips/docx, internal planning documents, tracked
  caches and `.DS_Store` files, stale timestamped benchmark outputs.

### Added

- `reproduce.sh`: one-command path from clean checkout to test suite plus
  regenerated benchmark report.
- `paper/research/`: novelty scan and threat-evidence brief with source URLs.

## [1.0.0] - 2026-01-24

### Added

- **Core Framework**
  - `EmbedGuard` main class for RAG security analysis
  - Cross-layer threat detection with weighted signal fusion
  - Three operational modes: passive, gated, active
  - Configurable thresholds and layer weights

- **Layer 1: Prompt Injection Detection**
  - DistilBERT-based neural classifier
  - 16 regex patterns for known injection signatures
  - 87.3% detection accuracy with 4.2ms latency
  - Batch detection support

- **Layer 2: Cryptographic Embedding Attestation**
  - TEE-based embedding generation (software simulation)
  - Cryptographic signing of embedding provenance
  - Certificate generation and verification
  - AMD SEV-SNP and Intel SGX support (hardware required)

- **Layer 3: Retrieval Distributional Analysis**
  - Incremental PCA for anomaly detection
  - KL divergence monitoring
  - Temporal rank correlation analysis
  - Baseline distribution tracking

- **Layer 4: Output Consistency Verification**
  - Perturbation-based stability testing
  - K=5 perturbations by default
  - Document removal, reordering, and noise injection strategies

- **Threat Correlation Engine**
  - Weighted signal fusion from all layers
  - Multi-layer attack correlation boost
  - Attack pattern analysis

- **Configuration System**
  - Preset configurations: high_security, balanced, low_latency
  - Custom threshold configuration
  - Per-layer weight adjustment
  - Enable/disable individual layers

- **CLI Interface**
  - `embedguard analyze` - Full security analysis
  - `embedguard check` - Quick injection detection
  - `embedguard benchmark` - Dataset benchmarking
  - JSON and text output formats

- **Examples**
  - Basic usage example
  - Advanced configuration example
  - RAG pipeline integration patterns

- **Testing**
  - Unit tests for core components
  - Prompt detection tests
  - Correlation engine tests
  - Shared test fixtures

### Performance

- 94.7% detection rate against optimization-based attacks
- 89.3% detection rate against adaptive attacks
- 51ms mean latency overhead
- 3.2% false positive rate

### Security

- Cross-layer detection provides 18.4pp improvement over single-layer
- Hardware-backed attestation transforms security to cryptographic verification
- Adaptive attack resilience with 27.9-35.1pp improvements over existing defenses

## [Unreleased]

### Planned

- PyPI package distribution
- Pre-trained prompt injection classifier
- GPU acceleration for neural components
- Streaming analysis mode
- Prometheus metrics integration
- Web dashboard for monitoring
