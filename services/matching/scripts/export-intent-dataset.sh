#!/usr/bin/env bash
# Export intent labels from core leads (placeholder for prod feedback loop).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${ROOT}/data/intent_export.jsonl"

echo "Export intent dataset stub — wire to core gRPC in production."
echo '{"text": "example spam lead", "label": "sell", "source": "spam"}' > "${OUT}"
echo "Wrote ${OUT}"
