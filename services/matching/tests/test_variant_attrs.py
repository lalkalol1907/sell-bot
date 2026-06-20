"""Tests for storage/color variant matching."""

import pytest


PRODUCT_256_BLACK = {
    "id": 1,
    "title": "iPhone 16 Pro 256GB Black",
    "keywords": ["iphone 16 pro 256 black"],
}

PRODUCT_128_WHITE = {
    "id": 2,
    "title": "iPhone 16 Pro 128GB White",
    "keywords": ["iphone 16 pro 128 white"],
}

PRODUCT_GENERIC = {
    "id": 3,
    "title": "iPhone 16 Pro",
    "keywords": ["iphone 16 pro"],
}


class TestVariantExtraction:
    def test_extract_storage_gb(self, reload_modules):
        from app.nlp.variant_attrs import extract_storage_gb

        assert extract_storage_gb("есть 16 про на 256?") == 256
        assert extract_storage_gb("куплю на 256гб") == 256
        assert extract_storage_gb("нужен 1tb") == 1024
        assert extract_storage_gb("куплю iphone 16") is None

    def test_extract_color(self, reload_modules):
        from app.nlp.variant_attrs import extract_color

        assert extract_color("нужен черный айфон") == "black"
        assert extract_color("white titanium 256") == "white"
        assert extract_color("куплю iphone 16") is None

    def test_variant_multiplier_missing_attrs(self, reload_modules):
        from app.nlp.variant_attrs import apply_variant_adjustment

        score = apply_variant_adjustment(1.0, "куплю 16 про 256 черный", PRODUCT_GENERIC)
        assert score < 0.8

    def test_variant_multiplier_exact_match(self, reload_modules):
        from app.nlp.variant_attrs import apply_variant_adjustment

        score = apply_variant_adjustment(1.0, "куплю 16 про 256 черный", PRODUCT_256_BLACK)
        assert score == 1.0

    def test_variant_multiplier_wrong_storage(self, reload_modules):
        from app.nlp.variant_attrs import apply_variant_adjustment

        score = apply_variant_adjustment(1.0, "куплю 16 про 256", PRODUCT_128_WHITE)
        assert score < 0.5


class TestVariantProductGate:
    def test_prefers_matching_storage_over_generic(self, reload_modules):
        from app.nlp.product_gate import match_product

        hit = match_product(
            "куплю iphone 16 pro 256",
            [PRODUCT_GENERIC, PRODUCT_256_BLACK, PRODUCT_128_WHITE],
        )
        assert hit is not None
        assert hit.product_id == 1

    def test_prefers_matching_color(self, reload_modules):
        from app.nlp.product_gate import match_product

        hit = match_product(
            "куплю iphone 16 pro 128 белый",
            [PRODUCT_256_BLACK, PRODUCT_128_WHITE],
        )
        assert hit is not None
        assert hit.product_id == 2

    def test_generic_message_keeps_generic_product(self, reload_modules):
        from app.nlp.product_gate import match_product

        hit = match_product("куплю iphone 16 pro", [PRODUCT_GENERIC, PRODUCT_256_BLACK])
        assert hit is not None
        assert hit.product_id in (1, 3)
