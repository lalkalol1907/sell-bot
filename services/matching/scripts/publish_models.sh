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

apply_aws_env() {
  export AWS_ACCESS_KEY_ID="${MODELS_S3_ACCESS_KEY:-${AWS_ACCESS_KEY_ID:-}}"
  export AWS_SECRET_ACCESS_KEY="${MODELS_S3_SECRET_KEY:-${AWS_SECRET_ACCESS_KEY:-}}"
  export AWS_DEFAULT_REGION="${MODELS_S3_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

s3_base_uri() {
  local bucket="${MODELS_S3_BUCKET:?MODELS_S3_BUCKET is required}"
  local prefix="${MODELS_S3_PREFIX:-}"
  prefix="${prefix#/}"
  prefix="${prefix%/}"
  if [[ -n "$prefix" ]]; then
    printf 's3://%s/%s/matching' "$bucket" "$prefix"
  else
    printf 's3://%s/matching' "$bucket"
  fi
}

aws_s3_args() {
  AWS_S3_ARGS=()
  if [[ -n "${MODELS_S3_ENDPOINT:-}" ]]; then
    AWS_S3_ARGS+=(--endpoint-url "$MODELS_S3_ENDPOINT")
  fi
}

upload_bundle() {
  local version="$1"
  local bundle_dir="$ROOT/models/bundles/$version"
  if [[ ! -d "$bundle_dir" ]]; then
    echo "Bundle directory not found: $bundle_dir" >&2
    exit 1
  fi

  require_cmd aws
  aws_s3_args

  local base
  base="$(s3_base_uri)"
  local dest="${base}/${version}/"
  echo "Uploading $bundle_dir -> $dest"
  aws s3 sync "$bundle_dir/" "$dest" "${AWS_S3_ARGS[@]}"

  if [[ "${PUBLISH_UPDATE_LATEST:-true}" == "true" ]]; then
    local latest_dest="${base}/latest.json"
    printf '{"version":"%s"}' "$version" | aws s3 cp - "$latest_dest" \
      "${AWS_S3_ARGS[@]}" \
      --content-type "application/json"
    echo "Updated $latest_dest"
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
apply_aws_env

PYTHON="${PYTHON:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
fi

BUILD_ARGS=(--version "$VERSION" --local-only)
if [[ "$SKIP_PARITY" == "true" ]]; then
  BUILD_ARGS+=(--skip-parity)
fi

echo "Building bundle $VERSION..."
"$PYTHON" "$ROOT/scripts/publish_models.py" "${BUILD_ARGS[@]}"

if [[ "$LOCAL_ONLY" == "true" ]]; then
  echo "Local bundle ready: $ROOT/models/bundles/$VERSION"
  exit 0
fi

upload_bundle "$VERSION"
echo "Published bundle $VERSION"
