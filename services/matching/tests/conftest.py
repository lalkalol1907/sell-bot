"""Pytest configuration for matching service."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _default_nlp_flags(monkeypatch):
    """Legacy pipeline by default; individual tests override."""
    monkeypatch.setenv("NLP_V2_ENABLED", "false")
    monkeypatch.setenv("NLP_V2_SEMANTIC", "false")
    monkeypatch.setenv("NLP_V2_NORMALIZE", "false")
    monkeypatch.setenv("NLP_V2_INTENT_ML", "false")

    import importlib

    import app.config

    importlib.reload(app.config)
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
        for name in (
            "app.config",
            "app.nlp.normalize",
            "app.nlp.intent_classifier",
            "app.nlp.product_gate",
            "app.nlp.scoring",
            "app.matcher",
            "app.normalize",
            "app.intent",
        ):
            importlib.reload(importlib.import_module(name))
        from app.nlp.intent_classifier import reset_model_cache

        reset_model_cache()

    return _reload
