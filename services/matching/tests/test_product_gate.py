"""Unit tests for product gate."""

import pytest

IPHONE = {"id": 1, "title": "iPhone 16", "keywords": ["айфон 16", "iphone 16"]}


class TestProductGate:
    def test_exact_keyword_match(self, reload_modules):
        from app.nlp.product_gate import match_product

        hit = match_product("куплю айфон 16", [IPHONE])
        assert hit is not None
        assert hit.product_id == 1
        assert hit.fuzzy_score >= 0.85

    def test_no_match_offtopic(self, reload_modules):
        from app.nlp.product_gate import match_product

        assert match_product("погода отличная", [IPHONE]) is None

    def test_semantic_mocked(self, monkeypatch, reload_modules):
        monkeypatch.setenv("NLP_V2_SEMANTIC", "true")

        class FakeHit:
            product_id = 1
            score = 0.8

        monkeypatch.setattr(
            "app.embeddings.indexer.search_products",
            lambda seller_id, text, products, limit=1: [FakeHit()],
        )
        reload_modules()
        from app.nlp.product_gate import match_product

        hit = match_product("где достать шестнадцатый про?", [IPHONE], seller_id=1)
        assert hit is not None
        assert hit.semantic_score >= 0.72

    def test_fuzzy_only_when_semantic_disabled(self, reload_modules):
        from app.nlp.product_gate import match_product

        hit = match_product("куплю айфон 16", [IPHONE])
        assert hit is not None
        assert hit.fuzzy_score >= 0.85
