"""Runtime configuration loaded from model bundle and environment."""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from pathlib import Path

from app.env import bool_env
from app.paths import models_dir

INTENT_MODEL_NAME = "intent.joblib"
INTENT_META_NAME = "intent.meta.json"
THRESHOLDS_NAME = "semantic_thresholds.json"

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)
EMBEDDING_MODEL_DIR = os.getenv("EMBEDDING_MODEL_DIR", "")
MODELS_LOCAL_DIR = os.getenv("MODELS_LOCAL_DIR", str(models_dir()))

VARIANT_STORAGE_MISMATCH_MULT = float(os.getenv("VARIANT_STORAGE_MISMATCH_MULT", "0.45"))
VARIANT_STORAGE_MISSING_MULT = float(os.getenv("VARIANT_STORAGE_MISSING_MULT", "0.72"))
VARIANT_COLOR_MISMATCH_MULT = float(os.getenv("VARIANT_COLOR_MISMATCH_MULT", "0.50"))
VARIANT_COLOR_MISSING_MULT = float(os.getenv("VARIANT_COLOR_MISSING_MULT", "0.78"))

INTENT_MODEL_PATH = os.getenv(
    "INTENT_MODEL_PATH",
    str(models_dir() / INTENT_MODEL_NAME),
)
SEMANTIC_THRESHOLDS_PATH = os.getenv(
    "SEMANTIC_THRESHOLDS_PATH",
    str(models_dir() / THRESHOLDS_NAME),
)

QDRANT_COLLECTION = "products"
EMBEDDING_DIM = 384

_lock = threading.RLock()


@dataclass(frozen=True)
class Thresholds:
    fuzzy_min: float
    semantic_min: float


_DEFAULT_THRESHOLDS = Thresholds(fuzzy_min=0.85, semantic_min=0.72)
_thresholds: Thresholds = _DEFAULT_THRESHOLDS


def load_thresholds(path: Path | None = None) -> Thresholds:
    global _thresholds
    target = path or Path(SEMANTIC_THRESHOLDS_PATH)
    if not target.is_file():
        with _lock:
            _thresholds = _DEFAULT_THRESHOLDS
        return _thresholds

    data = json.loads(target.read_text(encoding="utf-8"))
    loaded = Thresholds(
        fuzzy_min=float(data.get("fuzzy_min_score", _DEFAULT_THRESHOLDS.fuzzy_min)),
        semantic_min=float(data.get("semantic_min_score", _DEFAULT_THRESHOLDS.semantic_min)),
    )
    with _lock:
        _thresholds = loaded
    return loaded


def get_thresholds() -> Thresholds:
    with _lock:
        return _thresholds


def fuzzy_min_score() -> float:
    return get_thresholds().fuzzy_min


def semantic_min_score() -> float:
    return get_thresholds().semantic_min


def should_sync_models() -> bool:
    if bool_env("MODELS_SKIP_S3"):
        return False
    return bool(os.getenv("MODELS_S3_BUCKET", "").strip())


# Load thresholds at import if file exists.
load_thresholds()
