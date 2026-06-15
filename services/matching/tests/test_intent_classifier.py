"""Unit tests for intent classifier."""

import pytest


class TestIntentClassifier:
    def test_heuristic_buy(self, reload_modules):
        from app.nlp.intent_classifier import classify_intent

        assert classify_intent("куплю айфон").label == "buy"

    def test_heuristic_sell(self, reload_modules):
        from app.nlp.intent_classifier import classify_intent

        assert classify_intent("продаю айфон").label == "sell"
        assert classify_intent("продаю айфон").score == -1.0

    def test_heuristic_discussion(self, reload_modules):
        from app.nlp.intent_classifier import classify_intent

        assert classify_intent("у меня айфон тормозит").label == "discussion"

    def test_heuristic_indirect(self, reload_modules):
        from app.nlp.intent_classifier import classify_intent

        result = classify_intent("есть айфон?")
        assert result.label == "buy"
        assert result.score == 0.55
