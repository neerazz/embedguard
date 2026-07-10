# Changelog

All notable changes to EmbedGuard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned

- PyPI package distribution
- Pre-trained prompt injection classifier
- GPU acceleration for neural components
- Streaming analysis mode
- Prometheus metrics integration
- Web dashboard for monitoring

## [1.2.0] - 2026-07-10

Evidence-integrity hardening for the open benchmark and manuscript v3.1. The
IJCESEN version-of-record results remain unchanged.

### Fixed

- The public benchmark now executes the package's production
  `PromptInjectionDetector` in pattern-only mode instead of a duplicated
  81-pattern implementation that had drifted from the package.
- Statistical analysis now derives Wilson intervals from observed confusion-
  matrix counts and fails closed when evidence is missing; synthetic scores,
  invalid comparator tests, and fallback paper values were removed.
- Benchmark JSON now records input/source SHA-256 hashes, the nearest source
  commit when available, runtime/dependency metadata, and timing scope.
- Manuscript claims now match the committed 83-pattern result artifact and
  distinguish deterministic classification counts from host-dependent timing.
- Default construction performs no implicit model request; neural prompt
  detection and semantic output similarity are explicit opt-ins.
- Gated decisions are held by the integration examples instead of allowing
  flagged requests to continue to generation.
- The target AMD SEV-SNP diagram now uses report-data binding and VCEK-chain
  verification rather than TPM-style PCR terminology.
- Real generated outputs are never compared with synthetic perturbation
  proxies; same-generator testing now requires an explicit caller callback.
- Retrieval PCA now fits accumulated embedding rows at warm-up instead of
  leaving zero-valued components or fitting only the latest query batch.
- Correlation boosts now require confidence-weighted elevation, so
  zero-confidence layer scores cannot manufacture an active-mode block.
- Public titles, citations, badges, dependency declarations, commands, and
  figure captions now agree on the v1.2.0 package boundary.

### Changed

- Heavy neural/vector dependencies moved to explicit `neural` and `vector`
  extras; the core install is model-free.
- The HMAC provenance simulator uses an ephemeral key unless the caller supplies
  one and no longer writes a key into the user's home directory by default.
- The simulator HMAC now binds the validity period and simulated platform
  metadata, preventing post-issuance expiry extension or metadata mutation.
- The generic CLI benchmark classifies by threat score independently of
  operational mode and computes FPR/FNR over benign/attack denominators.
- The architecture figure's worked fusion arithmetic and the target SEV-SNP
  figure's nonce, replay, report-signature, and verification steps now match
  the implementation and protocol text.

### Removed

- Unsupported JailbreakBench/GCG/PAIR/AutoDAN/TAP result claims.
- Estimated pattern-count, neural, and Tier-2 cross-layer ablation tables.
- Unsupported institutional-review exemption and pre-built-container claims.
- Unsupported README comparator and unmeasured operational storage/review-time
  claims.

### Added

- `tests/test_evidence_integrity.py` guards benchmark/package parity and
  observed-count-only statistical analysis.
- Canonical v1.2.0 benchmark artifacts and count-based uncertainty output.
- A documented browser-rendered manuscript PDF and machine-readable Tier-1
  ablation transcription; the transcription is explicitly non-causal and is
  not presented as open reproduction.

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
  - Pattern detector plus optional neural-classifier scaffolding; no fine-tuned
    neural checkpoint was distributed
  - 16 regex patterns for known injection signatures
  - Batch detection support
  - Historical metadata claimed 87.3% detection and 4.2ms latency, but no raw
    result artifact was archived; v1.2 does not treat those values as evidence

- **Layer 2: Software Provenance Simulation**
  - HMAC-based embedding provenance simulation
  - Cryptographic signing of embedding provenance
  - Certificate generation and verification
  - AMD SEV-SNP remained an architectural target; no hardware integration shipped

- **Layer 3: Retrieval Distributional Analysis**
  - Incremental PCA for anomaly detection
  - Distribution-distance monitoring (legacy API uses `kl_divergence` naming;
    implementation computes Mahalanobis distance)
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

### Published Reference Performance

The associated article reported the following Tier-1 values; the v1.0.0 archive
did not contain the production corpus, raw predictions, or hardware logs needed
to reproduce them:

- 94.7% detection rate against optimization-based attacks
- 89.3% detection rate against adaptive attacks
- 51ms mean latency overhead
- 3.2% false positive rate

### Proposed Security Architecture

- The article reported an 18.4pp cross-layer improvement; the open archive did
  not include the ablation outputs needed to reproduce it
- Hardware-backed attestation was a target design, not a v1.0.0 package capability
- Historical 27.9-35.1pp comparator claims lacked open baseline outputs and are
  not retained as current evidence
