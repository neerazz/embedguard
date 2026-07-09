#!/usr/bin/env bash
# Reproduce the EmbedGuard benchmark results reported in the paper.
#
# Usage:
#   ./reproduce.sh          # set up env, run tests, run benchmarks
#
# Outputs land in results/ as timestamped benchmark_report_*.md /
# benchmark_results_*.json files. The committed
# results/benchmark_report_20260125_005427.md is the canonical run
# referenced by the paper.

set -euo pipefail
cd "$(dirname "$0")"

PYTHON=${PYTHON:-python3}

if [ ! -d .venv ]; then
    "$PYTHON" -m venv .venv
fi
.venv/bin/pip install -q -e ".[dev]"

echo "== Unit tests =="
.venv/bin/python -m pytest -q --no-cov

echo "== Benchmarks =="
.venv/bin/python examples/run_benchmarks.py

echo "Done. See results/ for the generated report."
