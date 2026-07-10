#!/usr/bin/env bash
# Repeat the open Tier-2 regression benchmark reported in manuscript v3.1.
#
# Usage:
#   ./reproduce.sh          # set up env, run tests, run benchmarks
#
# Outputs land in ${RESULTS_DIR:-results}/ as timestamped benchmark_report_*.md /
# benchmark_results_*.json files plus statistical_analysis.json. The committed
# results/benchmark_report_20260710_025640.md is the canonical v1.2.0 run
# referenced by manuscript v3.1.

set -euo pipefail
cd "$(dirname "$0")"

RESULTS_DIR=${RESULTS_DIR:-results}

select_python() {
    local candidates=()
    if [ -n "${PYTHON:-}" ]; then
        candidates+=("$PYTHON")
    else
        candidates+=(python3.14 python3.13 python3.12 python3.11 python3.10 python3)
    fi

    local candidate
    for candidate in "${candidates[@]}"; do
        if command -v "$candidate" >/dev/null 2>&1 \
            && "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' 2>/dev/null; then
            command -v "$candidate"
            return 0
        fi
    done
    return 1
}

PYTHON_BIN=$(select_python) || {
    echo "EmbedGuard reproduction requires Python 3.10 or newer." >&2
    echo "Install a supported Python or set PYTHON=/path/to/python." >&2
    exit 2
}

if [ -x .venv/bin/python ] \
    && ! .venv/bin/python -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
    echo "Replacing incompatible .venv (Python < 3.10)."
    rm -rf .venv
fi

if [ ! -x .venv/bin/python ]; then
    rm -rf .venv
    "$PYTHON_BIN" -m venv .venv
fi
.venv/bin/python -m pip install -q --upgrade "pip>=24" "setuptools>=68" wheel
.venv/bin/python -m pip install -q -e ".[dev]"

echo "== Unit tests =="
.venv/bin/python -m pytest -q --no-cov

echo "== Benchmarks =="
.venv/bin/python examples/run_benchmarks.py --results-dir "$RESULTS_DIR"

echo "== Count-based uncertainty =="
.venv/bin/python scripts/statistical_tests.py \
    --results "$RESULTS_DIR/latest_results.json" \
    --output "$RESULTS_DIR/statistical_analysis.json"

echo "Done. See $RESULTS_DIR for the generated report."
