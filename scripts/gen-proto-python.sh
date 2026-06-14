#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROTO_DIR="$ROOT/proto"
OUT_DIR="$ROOT/services/matching/app/generated"
mkdir -p "$OUT_DIR"
python3 -m grpc_tools.protoc \
  -I"$PROTO_DIR" \
  --python_out="$OUT_DIR" \
  --grpc_python_out="$OUT_DIR" \
  "$PROTO_DIR"/*.proto

# Fix relative imports in generated grpc files
for f in "$OUT_DIR"/*_pb2_grpc.py; do
  [[ -f "$f" ]] || continue
  if [[ "$(uname)" == "Darwin" ]]; then
    sed -i '' 's/^import \([a-z_]*\)_pb2/from app.generated import \1_pb2/' "$f"
  else
    sed -i 's/^import \([a-z_]*\)_pb2/from app.generated import \1_pb2/' "$f"
  fi
done

touch "$OUT_DIR/__init__.py"
echo "Python stubs -> $OUT_DIR"
