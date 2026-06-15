#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROTO_DIR="$ROOT/proto"
OUT_DIR="$ROOT/services/http-gateway/lib/grpc/generated"

mkdir -p "$OUT_DIR"

if command -v grpc_ruby_plugin >/dev/null 2>&1; then
  PLUGIN="$(command -v grpc_ruby_plugin)"
elif [ -n "${BUNDLE_GEMFILE:-}" ] || [ -f "$ROOT/services/http-gateway/Gemfile" ]; then
  PLUGIN="$(cd "$ROOT/services/http-gateway" && bundle show grpc-tools 2>/dev/null)/bin/x86_64-linux/grpc_ruby_plugin"
  if [ ! -x "$PLUGIN" ]; then
    ARCH="$(uname -m)"
    case "$ARCH" in
      arm64|aarch64) PLUGIN="$(cd "$ROOT/services/http-gateway" && bundle show grpc-tools)/bin/x86_64-linux/grpc_ruby_plugin" ;;
      x86_64) PLUGIN="$(cd "$ROOT/services/http-gateway" && bundle show grpc-tools)/bin/x86_64-linux/grpc_ruby_plugin" ;;
    esac
  fi
else
  GEM_DIR="$(gem which grpc-tools 2>/dev/null | sed 's|/lib/grpc.*||')"
  PLUGIN="$GEM_DIR/bin/x86_64-linux/grpc_ruby_plugin"
fi

if [ ! -x "$PLUGIN" ]; then
  echo "grpc_ruby_plugin not found; install grpc-tools gem" >&2
  exit 1
fi

protoc \
  -I "$PROTO_DIR" \
  --ruby_out="$OUT_DIR" \
  --grpc_out="$OUT_DIR" \
  --plugin="protoc-gen-grpc=$PLUGIN" \
  "$PROTO_DIR/catalog.proto" \
  "$PROTO_DIR/leads.proto" \
  "$PROTO_DIR/workers.proto" \
  "$PROTO_DIR/worker_login.proto"

echo "Ruby gRPC stubs written to $OUT_DIR"
