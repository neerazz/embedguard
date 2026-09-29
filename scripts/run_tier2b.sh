#!/usr/bin/env bash
# Run the Tier-2b PoisonedRAG benchmark grid reported in manuscript v3.2 §4.3.
#
# Usage:
#   python scripts/fetch_tier2b_data.py --data-dir data/tier2b   # ~765 MB, SHA-256 checked
#   PYTHON=.venv/bin/python scripts/run_tier2b.sh data/tier2b
#
# Needs the neural extra (sentence-transformers, torch) and pyarrow:
#   pip install -e ".[neural]" pyarrow
# Each configuration takes about one minute on an Apple M-series GPU and
# several minutes on CPU. Results land in results/tier2b_poisonedrag_*.{json,md}.

set -euo pipefail
cd "$(dirname "$0")/.."

DATA_DIR=${1:-data/tier2b}
PYTHON=${PYTHON:-python}

for form in blackbox stealth; do
    for per_target in 5 3 1; do
        echo "== ${form}, ${per_target} poison passage(s) per target"
        "$PYTHON" scripts/tier2b_poisonedrag.py \
            --data-dir "$DATA_DIR" \
            --distractors 5000 \
            --poison-form "$form" \
            --poison-per-target "$per_target" > /dev/null
    done
done
ls results/tier2b_poisonedrag_*
