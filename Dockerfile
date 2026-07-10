# EmbedGuard local container recipe
# Repeats the open Tier-2 prompt-detector benchmark only.
#
# Build:
#   docker build -t embedguard:local .
#
# Run the open regression benchmark:
#   docker run --rm embedguard:local
#
# Run specific benchmarks:
#   docker run --rm embedguard:local python examples/run_benchmarks.py --injection
#   docker run --rm embedguard:local python examples/run_benchmarks.py --benchmark nq

FROM python:3.10-slim@sha256:e5300dc020a26a34a19337a57602955a2510e22abeb176edd6de6cd2cc927dd4

# Metadata
LABEL org.opencontainers.image.title="EmbedGuard"
LABEL org.opencontainers.image.description="Cross-Layer Detection and Provenance Attestation for RAG Systems"
LABEL org.opencontainers.image.version="1.2.0"
LABEL org.opencontainers.image.authors="Neeraj Kumar Singh Beshane"
LABEL org.opencontainers.image.source="https://github.com/neerazz/embedguard"
LABEL org.opencontainers.image.licenses="MIT"

# Set working directory
WORKDIR /embedguard

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY embedguard/ embedguard/
COPY examples/ examples/
COPY data/ data/
COPY scripts/ scripts/
COPY pyproject.toml .
COPY README.md .
COPY LICENSE .

# Create a writable results directory and drop root privileges.
RUN mkdir -p results && chown -R 65532:65532 /embedguard
USER 65532:65532

# Set environment variables for reproducibility
ENV EMBEDGUARD_SEED=42
ENV PYTHONPATH=/embedguard
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Default command: run all benchmarks
CMD ["python", "examples/run_benchmarks.py", "--all"]

# Alternative entrypoints:
# Run injection benchmark only:
#   docker run --rm embedguard:local python examples/run_benchmarks.py --injection
#
# Run specific benign benchmark:
#   docker run --rm embedguard:local python examples/run_benchmarks.py --benchmark nq
#
# Run statistical tests:
#   docker run --rm embedguard:local sh -c \
#     'python examples/run_benchmarks.py --all && python scripts/statistical_tests.py \
#      --results results/latest_results.json --output results/statistical_analysis.json'
#
# Interactive shell:
#   docker run -it --rm embedguard:local /bin/bash
