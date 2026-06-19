#!/usr/bin/env bash
# Production intent training: calibrate thresholds + train classifier (embeddings).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

PYTHON="${PYTHON:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
fi

run() {
  echo "==> $*"
  "$PYTHON" "$@"
}

run "$ROOT/scripts/calibrate_semantic.py"
run "$ROOT/scripts/retrain_intent.py"

echo ""
echo "Training complete. Publish with:"
echo "  make publish MODELS_VERSION=2026.06.19-1"
