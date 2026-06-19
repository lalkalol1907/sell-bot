#!/usr/bin/env bash
# Build matching model bundle and publish to S3-compatible storage.
# Reads MODELS_S3_* (and AWS_* fallbacks) from repo .env by default.
#
# Usage:
#   ./scripts/publish_models.sh 2026.06.15-1
#   ./scripts/publish_models.sh 2026.06.15-1 --skip-parity
#   ./scripts/publish_models.sh --local-only dev-1
#   ENV_FILE=/path/to/.env ./scripts/publish_models.sh prod-1
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$ROOT/../.." && pwd)"

load_env() {
  local env_file="${ENV_FILE:-$REPO_ROOT/.env}"
  if [[ -f "$env_file" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$env_file"
    set +a
    echo "Loaded env from $env_file"
  else
    echo "No .env at $env_file (using current environment)" >&2
  fi
}

LOCAL_ONLY=false
SKIP_PARITY=false
VERSION=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --local-only)
      LOCAL_ONLY=true
      shift
      ;;
    --skip-parity)
      SKIP_PARITY=true
      shift
      ;;
    -h|--help)
      sed -n '2,8p' "$0"
      exit 0
      ;;
    *)
      if [[ -z "$VERSION" ]]; then
        VERSION="$1"
      else
        echo "Unknown argument: $1" >&2
        exit 1
      fi
      shift
      ;;
  esac
done

if [[ -z "$VERSION" ]]; then
  echo "Usage: $0 <version> [--skip-parity] | --local-only <version>" >&2
  exit 1
fi

load_env

PYTHON="${PYTHON:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
fi

BUILD_ARGS=(--version "$VERSION")
if [[ "$LOCAL_ONLY" == "true" ]]; then
  BUILD_ARGS+=(--local-only)
fi
if [[ "$SKIP_PARITY" == "true" ]]; then
  BUILD_ARGS+=(--skip-parity)
fi
if [[ "${PUBLISH_UPDATE_LATEST:-true}" != "true" ]]; then
  BUILD_ARGS+=(--no-latest)
fi

echo "Publishing bundle $VERSION..."
"$PYTHON" "$ROOT/scripts/publish_models.py" "${BUILD_ARGS[@]}"
