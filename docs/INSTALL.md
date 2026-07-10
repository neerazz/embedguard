# Installation Guide

## System Requirements

- **Python**: 3.10 or higher
- **Operating System**: Linux, macOS, or Windows
- **Memory/Disk**: depend on optional ML models; the default pattern path does not download a checkpoint

## Installation Methods

### Method 1: Docker (Recommended for Reproducibility)

The easiest way to run the model-free core and Tier-2 benchmark dependencies:

```bash
# Build the image locally from the included Dockerfile
git clone https://github.com/neerazz/embedguard.git
cd embedguard
docker build -t embedguard:latest .

# Run benchmarks
docker run --rm embedguard:latest python examples/run_benchmarks.py --all

# Interactive shell
docker run -it --rm embedguard:latest /bin/bash
```

### Method 2: From Source (Development)

```bash
# Clone the repository
git clone https://github.com/neerazz/embedguard.git
cd embedguard

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package and development tools
pip install -e '.[dev]'

# Verify installation
python -c "import embedguard; print('EmbedGuard installed successfully')"
```

### Method 3: Direct Installation

`requirements.txt` contains the core runtime set for environments that do not install from `pyproject.toml`:

```bash
pip install -r requirements.txt
pip install -e . --no-deps
```

## Dependencies

Core package dependencies:

| Package | Version | Purpose |
|---------|---------|---------|
| numpy | >=1.24.0 | Numerical computing |
| scipy | >=1.10.0 | Scientific computing |
| scikit-learn | >=1.3.0 | Machine learning utilities |
| pydantic | >=2.0.0 | Data validation |
| loguru | >=0.7.0 | Logging |

Optional model paths are explicit extras; the default install performs no model download:

```bash
pip install -e '.[neural]'  # PyTorch, Transformers, Sentence-Transformers
pip install -e '.[vector]'  # FAISS CPU
```

## Verifying Installation

Run the test suite to verify everything works:

```bash
# Run all tests
python -m pytest tests/ -v

# Run quick smoke test
python -c "
from embedguard import EmbedGuard
guard = EmbedGuard()
result = guard.analyze('What is Python?', [])
print(f'Installation verified! Decision: {result.decision.value}')
"
```

## Running the Open Tier-2 Regression Benchmark

To repeat the open 135-sample prompt-detector observations (not the Tier-1 paper results):

```bash
# Full benchmark suite
python examples/run_benchmarks.py --all

# Individual benchmarks
python examples/run_benchmarks.py --injection
python examples/run_benchmarks.py --benchmark nq
python examples/run_benchmarks.py --benchmark hotpotqa
python examples/run_benchmarks.py --benchmark msmarco
```

Expected classification counts for the committed inputs:
- Detection Rate: 100% (30/30 attacks)
- False Positive Rate: 0% (0/105 benign)
- Latency: host-dependent; inspect the generated JSON

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'embedguard'`
**Solution**: Ensure you're in the project root and run `pip install -e .`

**Issue**: CUDA/GPU errors
**Solution**: EmbedGuard runs on CPU by default. For GPU support, install PyTorch with CUDA.

**Issue**: Memory errors with large datasets
**Solution**: Reduce batch size in configuration or use Docker with memory limits.

### Getting Help

- GitHub Issues: https://github.com/neerazz/embedguard/issues
- Documentation: See `docs/USAGE.md` for detailed usage guide

## Hardware-Attestation Status

The released package does not integrate with AMD SEV-SNP or Intel SGX hardware. `EmbeddingAttestationLayer` is an HMAC software simulator for development and certificate-plumbing tests. Implementing the target hardware-rooted protocol requires a separate attestation client, endorsement-chain verification, freshness/nonces, and platform-policy validation; installing this package on a TEE-capable host does not add those controls automatically.
