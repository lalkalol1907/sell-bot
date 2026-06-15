"""Unit tests for normalize v2."""

import os

import pytest


@pytest.fixture
def v2_normalize(monkeypatch, reload_modules):
    monkeypatch.setenv("NLP_V2_NORMALIZE", "true")
    reload_modules()
    from app.nlp.normalize import normalize_text

    return normalize_text


class TestNormalizeV2:
    def test_lemmatize_kuplyu(self, v2_normalize):
        result = v2_normalize("куплю айфон")
        assert "купить" in result
        assert "айфон" in result

    def test_translit_iphone(self, v2_normalize):
        result = v2_normalize("Куплю iPhone 16")
        assert "айфон" in result
        assert "iphone" in result

    def test_emoji_removed(self, v2_normalize):
        result = v2_normalize("куплю 🔥 айфон")
        assert "🔥" not in result

    def test_empty(self, v2_normalize):
        assert v2_normalize("") == ""

    def test_samsung_translit(self, v2_normalize):
        from app.nlp.normalize import translit_expand

        assert "samsung" in translit_expand("самсунг s24") or "самсунг" in translit_expand("samsung s24")
