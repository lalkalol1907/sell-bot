"""Pytest configuration for matching service."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _reset_runtime(monkeypatch):
    from app.config import INTENT_MODEL_NAME, THRESHOLDS_NAME, load_thresholds
    from app.paths import models_dir

    root = models_dir()
    thresholds = root / THRESHOLDS_NAME
    if thresholds.is_file():
        monkeypatch.setenv("SEMANTIC_THRESHOLDS_PATH", str(thresholds))
        load_thresholds(thresholds)

    intent = root / INTENT_MODEL_NAME
    if intent.is_file():
        monkeypatch.setenv("INTENT_MODEL_PATH", str(intent))
    else:
        legacy = root / "intent_v1.joblib"
        if legacy.is_file():
            monkeypatch.setenv("INTENT_MODEL_PATH", str(legacy))

    yield

    for key in ("INTENT_MODEL_PATH", "EMBEDDING_MODEL_DIR", "SEMANTIC_THRESHOLDS_PATH"):
        os.environ.pop(key, None)
    try:
        from app.embeddings.encoder import reset_encoder_cache
        from app.embeddings.indexer import reset_index_cache
        from app.models_runtime import reset_runtime_state
        from app.nlp.intent_classifier import reset_model_cache

        reset_runtime_state()
        reset_model_cache()
        reset_encoder_cache()
        reset_index_cache("unknown")
    except Exception:
        pass


@pytest.fixture
def reload_modules():
    import importlib

    def _reload():
        from app.config import load_thresholds

        load_thresholds()
        for name in (
            "app.config",
            "app.nlp.normalize",
            "app.nlp.intent_classifier",
            "app.nlp.product_gate",
            "app.nlp.scoring",
            "app.pipeline.orchestrator",
        ):
            importlib.reload(importlib.import_module(name))
        from app.nlp.intent_classifier import reset_model_cache

        reset_model_cache()

    return _reload
