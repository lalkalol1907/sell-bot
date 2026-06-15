"""Additional product gate and scoring coverage."""

import pytest


def test_product_gate_empty_products(reload_modules):
    from app.nlp.product_gate import match_product

    assert match_product("куплю айфон", []) is None


def test_scoring_no_product_threshold(reload_modules):
    from app.nlp.intent_classifier import IntentResult
    from app.nlp.scoring import compute_level

    result = compute_level(0.5, IntentResult("buy", 0.9), "precise")
    assert not result.matched
    assert result.reject_reason == "no_product"


def test_scoring_discussion_aggressive(reload_modules):
    from app.nlp.intent_classifier import IntentResult
    from app.nlp.scoring import compute_level

    result = compute_level(0.9, IntentResult("discussion", 0.1), "aggressive", fuzzy_score=0.9)
    assert result.matched
    assert result.level == "probable"
