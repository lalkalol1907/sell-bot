"""HTTP health and metrics endpoints."""

from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.models_runtime import current_version

app = FastAPI(title="sellbot-matching")


@app.get("/health")
def health():
    return {"status": "ok", "models_version": current_version()}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
