# Installation Guide

## System Requirements

- **Python**: 3.10 or higher
- **Operating System**: Linux, macOS, or Windows
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Disk Space**: 500MB for installation

## Installation Methods

### Method 1: Docker (Recommended for Reproducibility)

The easiest way to run EmbedGuard with all dependencies:

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

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .

# Verify installation
python -c "import embedguard; print('EmbedGuard installed successfully')"
```

### Method 3: Direct Installation

```bash
pip install -r requirements.txt
```

## Dependencies

Core dependencies (from `requirements.txt`):

| Package | Version | Purpose |
|---------|---------|---------|
| torch | >=2.0.0 | Deep learning framework |
| transformers | >=4.30.0 | NLP models |
| sentence-transformers | >=2.2.0 | Embedding generation |
| numpy | >=1.24.0 | Numerical computing |
| scipy | >=1.10.0 | Scientific computing |
| scikit-learn | >=1.3.0 | Machine learning utilities |
| faiss-cpu | >=1.7.4 | Vector similarity search |
| pydantic | >=2.0.0 | Data validation |
| loguru | >=0.7.0 | Logging |

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

## Running Benchmarks

To reproduce the paper results:

```bash
# Full benchmark suite
python examples/run_benchmarks.py --all

# Individual benchmarks
python examples/run_benchmarks.py --injection
python examples/run_benchmarks.py --nq
python examples/run_benchmarks.py --hotpotqa
python examples/run_benchmarks.py --msmarco
```

Expected output:
- Detection Rate: 100% (30/30 attacks)
- False Positive Rate: 0% (0/105 benign)
- Mean Latency: ~0.05ms

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

## Hardware Requirements for TEE

The TEE (Trusted Execution Environment) layer requires:
- AMD SEV-SNP compatible processor, OR
- Intel SGX compatible processor

Without TEE hardware, EmbedGuard runs in software simulation mode (default).
