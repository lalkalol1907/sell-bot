"""Unit tests for scoring."""

import pytest

from app.nlp.intent_classifier import IntentResult
from app.nlp.scoring import compute_level


class TestScoring:
    def test_sell_reject(self):
        result = compute_level(0.9, IntentResult("sell", -1.0), "precise")
        assert not result.matched
        assert result.reject_reason == "sell_intent"

    def test_confirmed_buy(self):
        result = compute_level(0.9, IntentResult("buy", 0.9), "precise", fuzzy_score=0.9)
        assert result.matched
        assert result.level == "confirmed"

    def test_balanced_high_intent_probable(self):
        result = compute_level(0.9, IntentResult("buy", 0.9), "balanced", fuzzy_score=0.9)
        assert result.matched
        assert result.level == "probable"

    def test_discussion_precise_reject(self):
        result = compute_level(0.9, IntentResult("discussion", 0.1), "precise", fuzzy_score=0.9)
        assert not result.matched
        assert result.reject_reason == "discussion"

    def test_discussion_aggressive_probable(self):
        result = compute_level(0.9, IntentResult("discussion", 0.1), "aggressive", fuzzy_score=0.9)
        assert result.matched
        assert result.level == "probable"

    def test_semantic_threshold_pass(self):
        result = compute_level(0.75, IntentResult("buy", 0.55), "balanced", semantic_score=0.75)
        assert result.matched

    def test_combined_formula(self):
        result = compute_level(1.0, IntentResult("buy", 0.9), "precise", fuzzy_score=1.0)
        assert abs(result.combined - (1.0 * 0.55 + 0.9 * 0.45)) < 0.001
