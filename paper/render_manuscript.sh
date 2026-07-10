#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
PAPER_DIR="$ROOT/paper"
SOURCE="$PAPER_DIR/manuscript.md"
CSS="$PAPER_DIR/manuscript.css"
OUTPUT=${1:-"$PAPER_DIR/manuscript.pdf"}

PANDOC_BIN=${PANDOC_BIN:-$(command -v pandoc || true)}
if [[ -z "$PANDOC_BIN" ]]; then
    echo "pandoc is required to render the manuscript" >&2
    exit 2
fi

if [[ -n "${CHROME_BIN:-}" ]]; then
    CHROME="$CHROME_BIN"
elif command -v google-chrome >/dev/null 2>&1; then
    CHROME=$(command -v google-chrome)
elif command -v chromium >/dev/null 2>&1; then
    CHROME=$(command -v chromium)
elif [[ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]]; then
    CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
else
    echo "Google Chrome or Chromium is required to print the manuscript PDF" >&2
    exit 2
fi

TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/embedguard-manuscript.XXXXXX")
trap 'rm -rf "$TMP_DIR"' EXIT
HTML="$TMP_DIR/manuscript.html"
PROFILE="$TMP_DIR/chrome-profile"
mkdir -p "$PROFILE" "$(dirname "$OUTPUT")"

cd "$PAPER_DIR"
"$PANDOC_BIN" manuscript.md \
    --from=gfm \
    --to=html5 \
    --standalone \
    --embed-resources \
    --css manuscript.css \
    --metadata pagetitle="EmbedGuard manuscript v3.1" \
    --output "$HTML"

rm -f "$OUTPUT"
"$CHROME" \
    --headless=new \
    --disable-gpu \
    --no-first-run \
    --no-default-browser-check \
    --no-pdf-header-footer \
    --allow-file-access-from-files \
    --user-data-dir="$PROFILE" \
    --print-to-pdf="$OUTPUT" \
    "file://$HTML" >/dev/null 2>&1 &
CHROME_PID=$!
DEADLINE=$((SECONDS + ${RENDER_TIMEOUT_SECONDS:-90}))
LAST_SIZE=-1
STABLE_CHECKS=0
while kill -0 "$CHROME_PID" 2>/dev/null; do
    SIZE=0
    if [[ -f "$OUTPUT" ]]; then
        SIZE=$(wc -c < "$OUTPUT" | tr -d ' ')
    fi
    if [[ "$SIZE" -gt 0 && "$SIZE" -eq "$LAST_SIZE" ]]; then
        STABLE_CHECKS=$((STABLE_CHECKS + 1))
        if [[ "$STABLE_CHECKS" -ge 4 ]]; then
            kill -TERM "$CHROME_PID" 2>/dev/null || true
            wait "$CHROME_PID" 2>/dev/null || true
            break
        fi
    else
        STABLE_CHECKS=0
        LAST_SIZE=$SIZE
    fi
    if [[ "$SECONDS" -ge "$DEADLINE" ]]; then
        kill -KILL "$CHROME_PID" 2>/dev/null || true
        wait "$CHROME_PID" 2>/dev/null || true
        echo "Chrome timed out before producing a stable PDF" >&2
        exit 1
    fi
    sleep 0.5
done

if [[ ! -s "$OUTPUT" ]]; then
    echo "manuscript PDF was not created: $OUTPUT" >&2
    exit 1
fi
printf 'Rendered %s\n' "$OUTPUT"
