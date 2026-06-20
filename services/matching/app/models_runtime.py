"""Runtime model bundle state and hot-reload."""

from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path

from prometheus_client import Counter, Info

from app.config import EMBEDDING_MODEL_NAME, load_thresholds
from app.models_sync import SyncResult, peek_remote_version, should_sync_models, sync_models_from_s3

logger = logging.getLogger(__name__)

_lock = threading.RLock()
_current_version: str | None = None

MODELS_RELOAD_TOTAL = Counter(
    "matching_models_reload_total",
    "Model bundle reload attempts",
    ["result"],
)
MODELS_VERSION_INFO = Info("matching_models", "Active model bundle version")


def current_version() -> str | None:
    with _lock:
        return _current_version


def reset_runtime_state() -> None:
    global _current_version
    with _lock:
        _current_version = None


def _validate_embedding_model(result: SyncResult) -> bool:
    manifest_path = result.local_dir / "manifest.json"
    if not manifest_path.is_file():
        return True

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    embedding_model = manifest.get("embedding_model", "")
    if embedding_model and embedding_model != EMBEDDING_MODEL_NAME:
        logger.error(
            "Refusing model reload: embedding_model %s differs from configured %s",
            embedding_model,
            EMBEDDING_MODEL_NAME,
        )
        return False
    return True


def apply_bundle(result: SyncResult) -> None:
    global _current_version

    if not _validate_embedding_model(result):
        raise RuntimeError(f"incompatible embedding model in bundle {result.version}")

    with _lock:
        if result.intent_model_path:
            os.environ["INTENT_MODEL_PATH"] = str(result.intent_model_path)
        if result.embedding_model_dir:
            os.environ["EMBEDDING_MODEL_DIR"] = str(result.embedding_model_dir)
        thresholds = result.local_dir / "semantic_thresholds.json"
        if thresholds.is_file():
            os.environ["SEMANTIC_THRESHOLDS_PATH"] = str(thresholds)
            load_thresholds(thresholds)

        from app.embeddings.encoder import reset_encoder_cache
        from app.embeddings.indexer import reset_index_cache
        from app.nlp.intent_classifier import reset_model_cache

        reset_encoder_cache()
        reset_model_cache()
        reset_index_cache(result.version)

        _current_version = result.version
        MODELS_VERSION_INFO.info({"version": result.version})
        logger.info("Active model bundle switched to %s", result.version)


def reload_if_changed() -> bool:
    """Check S3 latest.json and reload if version changed."""
    if not should_sync_models():
        return False
    if os.getenv("MODELS_S3_VERSION", "").strip():
        return False

    try:
        remote_version = peek_remote_version()
    except Exception:
        logger.exception("Failed to peek remote model version")
        MODELS_RELOAD_TOTAL.labels(result="error").inc()
        return False

    if remote_version is None:
        return False

    with _lock:
        if remote_version == _current_version:
            return False

    try:
        result = sync_models_from_s3(version=remote_version)
        if result is None:
            return False
        apply_bundle(result)
        MODELS_RELOAD_TOTAL.labels(result="success").inc()
        return True
    except Exception:
        logger.exception("Failed to reload model bundle %s", remote_version)
        MODELS_RELOAD_TOTAL.labels(result="error").inc()
        return False
