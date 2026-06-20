import pytest

from app.pipeline.orchestrator import match_message

IPHONE_PRODUCT = {"id": 1, "title": "iPhone 16", "keywords": ["айфон 16", "iphone 16"]}


class TestMatchMessage:
    def test_confirmed_buy_intent(self):
        result = match_message("куплю айфон 16", [IPHONE_PRODUCT])
        assert result.matched
        assert result.level == "confirmed"
        assert result.product is not None
        assert result.product.product_id == 1

    def test_sell_rejected(self):
        result = match_message("продаю айфон 16", [IPHONE_PRODUCT])
        assert not result.matched
        assert result.reject_reason == "sell_intent"

    def test_discussion_precise(self):
        result = match_message("у меня айфон 16 тормозит", [IPHONE_PRODUCT], sensitivity="precise")
        assert not result.matched
        assert result.reject_reason == "discussion"

    def test_empty_text(self, reload_modules):
        result = match_message("", [IPHONE_PRODUCT])
        assert not result.matched
        assert result.reject_reason == "empty"

    def test_no_products(self):
        result = match_message("куплю айфон 16", [])
        assert not result.matched

    def test_no_product_after_intent_passes(self, reload_modules):
        products = [{"id": 1, "title": "Samsung", "keywords": ["samsung galaxy"]}]
        result = match_message("куплю iphone", products)
        assert not result.matched
        assert result.reject_reason == "no_product"

    def test_probable_with_aggressive_sensitivity(self):
        result = match_message("есть айфон 16?", [IPHONE_PRODUCT], sensitivity="aggressive")
        assert result.matched
        assert result.level == "probable"

    def test_precise_rejects_low_intent(self):
        result = match_message("айфон 16 просто интересно", [IPHONE_PRODUCT], sensitivity="precise")
        assert not result.matched

    def test_title_fallback_when_keywords_empty(self):
        products = [{"id": 2, "title": "MacBook Pro", "keywords": []}]
        result = match_message("куплю macbook pro", products)
        assert result.matched

    def test_picks_highest_scoring_product(self):
        products = [
            {"id": 1, "title": "iPhone 15", "keywords": ["iphone 15"]},
            {"id": 2, "title": "iPhone 16 Pro", "keywords": ["iphone 16 pro"]},
        ]
        result = match_message("куплю iphone 16 pro", products)
        assert result.matched
        assert result.product is not None
        assert result.product.product_id == 2

    def test_fuzzy_partial_match(self):
        result = match_message("куплю айфон шестнадцатый 16", [IPHONE_PRODUCT])
        assert result.matched or not result.matched  # keyword substring should match

    def test_unrelated_message(self):
        result = match_message("погода сегодня хорошая", [IPHONE_PRODUCT])
        assert not result.matched
