"""Tests for model watcher."""

from unittest.mock import patch


def test_should_watch_models_default_when_s3_unpinned(monkeypatch):
    monkeypatch.setenv("MODELS_S3_BUCKET", "sellbot")
    monkeypatch.setenv("NLP_V2_SEMANTIC", "true")
    monkeypatch.delenv("MODELS_S3_VERSION", raising=False)
    monkeypatch.delenv("MODELS_WATCH_ENABLED", raising=False)
    monkeypatch.delenv("MODELS_SKIP_S3", raising=False)

    from app.models_watcher import should_watch_models

    assert should_watch_models() is True


def test_should_watch_models_disabled_when_pinned(monkeypatch):
    monkeypatch.setenv("MODELS_S3_BUCKET", "sellbot")
    monkeypatch.setenv("MODELS_S3_VERSION", "2026.06.19-1")
    monkeypatch.setenv("NLP_V2_SEMANTIC", "true")

    from app.models_watcher import should_watch_models

    assert should_watch_models() is False


def test_should_watch_models_respects_explicit_disable(monkeypatch):
    monkeypatch.setenv("MODELS_S3_BUCKET", "sellbot")
    monkeypatch.setenv("NLP_V2_SEMANTIC", "true")
    monkeypatch.setenv("MODELS_WATCH_ENABLED", "false")

    from app.models_watcher import should_watch_models

    assert should_watch_models() is False


def test_start_models_watcher_starts_thread(monkeypatch):
    monkeypatch.setenv("MODELS_S3_BUCKET", "sellbot")
    monkeypatch.setenv("NLP_V2_SEMANTIC", "true")

    from app import models_watcher

    with patch.object(models_watcher, "should_watch_models", return_value=True):
        with patch.object(models_watcher.threading, "Thread") as thread_cls:
            thread_cls.return_value.start = lambda: None
            models_watcher.start_models_watcher()
            thread_cls.assert_called_once()
