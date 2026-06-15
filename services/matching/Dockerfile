FROM python:3.14-slim AS model-cache
RUN pip install --no-cache-dir sentence-transformers
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"

FROM python:3.14-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends protobuf-compiler && rm -rf /var/lib/apt/lists/*
COPY proto/ ./proto/
COPY services/matching/ ./services/matching/
WORKDIR /build/services/matching
RUN pip install --no-cache-dir . && \
    python -m grpc_tools.protoc \
      -I../../proto \
      --python_out=./app/generated \
      --grpc_python_out=./app/generated \
      ../../proto/*.proto && \
    touch app/generated/__init__.py && \
    for f in app/generated/*_pb2_grpc.py; do \
      sed -i 's/^import \(.*\)_pb2/from app.generated import \1_pb2/' "$f"; \
    done

FROM python:3.14-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /build/services/matching/app ./app
COPY --from=builder /build/services/matching/data ./data
COPY --from=builder /build/services/matching/models ./models
COPY --from=model-cache /root/.cache/huggingface /root/.cache/huggingface
ENV PYTHONPATH=/app
EXPOSE 50052 8000
CMD ["python", "-m", "app.main"]
