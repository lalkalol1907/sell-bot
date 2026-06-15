"""NLP v2 configuration from environment."""

from __future__ import annotations

import os


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


NLP_V2_ENABLED = _bool("NLP_V2_ENABLED", False)
NLP_V2_NORMALIZE = _bool("NLP_V2_NORMALIZE", False)
NLP_V2_SEMANTIC = _bool("NLP_V2_SEMANTIC", True)
NLP_V2_INTENT_ML = _bool("NLP_V2_INTENT_ML", True)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)

FUZZY_MIN_SCORE = float(os.getenv("FUZZY_MIN_SCORE", "0.85"))
SEMANTIC_MIN_SCORE = float(os.getenv("SEMANTIC_MIN_SCORE", "0.72"))

VARIANT_STORAGE_MISMATCH_MULT = float(os.getenv("VARIANT_STORAGE_MISMATCH_MULT", "0.45"))
VARIANT_STORAGE_MISSING_MULT = float(os.getenv("VARIANT_STORAGE_MISSING_MULT", "0.72"))
VARIANT_COLOR_MISMATCH_MULT = float(os.getenv("VARIANT_COLOR_MISMATCH_MULT", "0.50"))
VARIANT_COLOR_MISSING_MULT = float(os.getenv("VARIANT_COLOR_MISSING_MULT", "0.78"))

INTENT_MODEL_PATH = os.getenv(
    "INTENT_MODEL_PATH",
    os.path.join(os.path.dirname(__file__), "..", "models", "intent_v1.joblib"),
)
SEMANTIC_THRESHOLDS_PATH = os.getenv(
    "SEMANTIC_THRESHOLDS_PATH",
    os.path.join(os.path.dirname(__file__), "..", "models", "semantic_thresholds.json"),
)

QDRANT_COLLECTION = "products"
EMBEDDING_DIM = 384
