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

    def test_heuristic_negated_sell_with_buy(self, reload_modules):
        from app.nlp.intent_classifier import classify_intent

        result = classify_intent("есть кто продаёт шестнадцатый? нет, ищу купить")
        assert result.label == "buy"
        assert result.score == 0.9


class TestIntentMerge:
    def test_merge_prefers_heuristic_sell(self):
        from app.nlp.intent_classifier import IntentResult, _merge_with_heuristic

        heuristic = IntentResult("sell", -1.0)
        ml = IntentResult("buy", 0.9)
        assert _merge_with_heuristic(heuristic, ml).label == "sell"

    def test_merge_caps_indirect_buy(self):
        from app.nlp.intent_classifier import IntentResult, _merge_with_heuristic

        heuristic = IntentResult("buy", 0.55)
        ml = IntentResult("buy", 0.9)
        assert _merge_with_heuristic(heuristic, ml).score == 0.55

    def test_merge_heuristic_buy_when_ml_none(self):
        from app.nlp.intent_classifier import IntentResult, _merge_with_heuristic

        heuristic = IntentResult("buy", 0.9)
        ml = IntentResult("none", 0.1)
        assert _merge_with_heuristic(heuristic, ml).label == "buy"

    def test_merge_heuristic_buy_blocks_ml_sell(self):
        from app.nlp.intent_classifier import IntentResult, _merge_with_heuristic

        heuristic = IntentResult("buy", 0.9)
        ml = IntentResult("sell", -1.0)
        assert _merge_with_heuristic(heuristic, ml).label == "buy"

    def test_listing_line_without_kuplyu_is_buy(self, reload_modules):
        from app.nlp.intent_classifier import classify_intent

        result = classify_intent("16 Pro Max 256 White")
        assert result.label == "buy"
        assert result.score == 0.55

    def test_desert_color_with_kuplyu_is_buy(self, reload_modules):
        from app.nlp.intent_classifier import classify_intent

        result = classify_intent("куплю айфон 16 про макс 8 128 десерт")
        assert result.label == "buy"
        assert result.score == 0.9

    def test_predlozhite_with_product_is_buy(self, reload_modules):
        from app.nlp.intent_classifier import classify_intent

        result = classify_intent("предложите iphone 16 pro max 1tb natural")
        assert result.label == "buy"
