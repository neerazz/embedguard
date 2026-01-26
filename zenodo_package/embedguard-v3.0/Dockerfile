# EmbedGuard Docker Image
# Enables one-line reproducibility of all paper results
#
# Usage:
#   docker build -t embedguard:v1.0 .
#   docker run --rm embedguard:v1.0 python -m src.evaluation.run_benchmarks
#
# Publish to GitHub Container Registry:
#   docker tag embedguard:v1.0 ghcr.io/neerazz/embedguard:v1.0
#   docker push ghcr.io/neerazz/embedguard:v1.0

FROM python:3.10-slim

# Metadata
LABEL org.opencontainers.image.title="EmbedGuard"
LABEL org.opencontainers.image.description="Cross-Layer Detection and Provenance Attestation for RAG Systems"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="Neeraj Kumar Singh Beshane"
LABEL org.opencontainers.image.source="https://github.com/neerazz/embedguard"
LABEL org.opencontainers.image.licenses="MIT"

# Set working directory
WORKDIR /embedguard

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ src/
COPY data/ data/
COPY scripts/ scripts/
COPY tests/ tests/
COPY pyproject.toml .
COPY README.md .
COPY LICENSE .

# Create results directory
RUN mkdir -p results

# Set environment variables for reproducibility
ENV EMBEDGUARD_SEED=42
ENV PYTHONPATH=/embedguard
ENV PYTHONUNBUFFERED=1

# Default command: run benchmarks
CMD ["python", "-m", "src.evaluation.run_benchmarks"]

# Alternative entrypoints:
# Run statistical tests:
#   docker run --rm embedguard:v1.0 python scripts/statistical_tests.py
#
# Run unit tests:
#   docker run --rm embedguard:v1.0 pytest tests/ -v
#
# Interactive shell:
#   docker run -it --rm embedguard:v1.0 /bin/bash
