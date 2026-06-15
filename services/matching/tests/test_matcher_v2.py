"""Matcher v2 orchestrator tests."""

import pytest

IPHONE = {"id": 1, "title": "iPhone 16", "keywords": ["айфон 16", "iphone 16"]}


@pytest.fixture
def v2_matcher(monkeypatch, reload_modules):
    monkeypatch.setenv("NLP_V2_ENABLED", "true")
    monkeypatch.setenv("NLP_V2_NORMALIZE", "true")
    monkeypatch.setenv("NLP_V2_INTENT_ML", "false")
    monkeypatch.setenv("NLP_V2_SEMANTIC", "false")
    reload_modules()
    from app.nlp.intent_classifier import reset_model_cache

    reset_model_cache()
    from app.matcher import match_message

    return match_message


class TestMatcherV2:
    def test_confirmed_buy(self, v2_matcher):
        result = v2_matcher("куплю айфон 16", [IPHONE])
        assert result.matched
        assert result.level == "confirmed"

    def test_sell_reject(self, v2_matcher):
        result = v2_matcher("продаю айфон 16", [IPHONE])
        assert not result.matched
        assert result.reject_reason == "sell_intent"

    def test_discussion_precise(self, v2_matcher):
        result = v2_matcher("у меня айфон 16 тормозит", [IPHONE], sensitivity="precise")
        assert not result.matched
        assert result.reject_reason == "discussion"
