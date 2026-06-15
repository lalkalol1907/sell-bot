"""Additional matcher orchestrator coverage."""

import pytest

IPHONE = {"id": 1, "title": "iPhone 16", "keywords": ["айфон 16", "iphone 16"]}


def test_product_passes_threshold():
    from app.matcher import product_passes_threshold

    assert product_passes_threshold(0.9, 0.0)
    assert product_passes_threshold(0.0, 0.75)
    assert not product_passes_threshold(0.5, 0.5)


def test_legacy_empty_text(reload_modules):
    from app.matcher import match_message

    result = match_message("", [IPHONE])
    assert not result.matched
    assert result.reject_reason == "empty"


def test_legacy_no_product_after_sell_check(reload_modules):
    from app.matcher import match_message

    result = match_message("куплю ps5", [])
    assert not result.matched
    assert result.reject_reason == "no_product"
