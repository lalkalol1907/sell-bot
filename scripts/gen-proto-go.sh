#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/services/worker-engine"
GEN="$OUT/internal/gen"
rm -rf "$GEN"

if ! command -v protoc-gen-go >/dev/null 2>&1 || ! command -v protoc-gen-go-grpc >/dev/null 2>&1; then
  echo "Installing protoc Go plugins..."
  go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.36.5
  go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.5.1
fi
export PATH="${PATH}:$(go env GOPATH)/bin"

for f in workers.proto worker_login.proto; do
  protoc -I"$ROOT/proto" \
    --go_out="$OUT" \
    --go_opt=module=github.com/sellbot/worker-engine \
    --go-grpc_out="$OUT" \
    --go-grpc_opt=module=github.com/sellbot/worker-engine \
    "$ROOT/proto/$f"
done
echo "Go stubs -> $GEN"
