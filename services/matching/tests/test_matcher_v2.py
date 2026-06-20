"""Matcher pipeline tests."""

import pytest

from app.pipeline.orchestrator import match_message

IPHONE = {"id": 1, "title": "iPhone 16", "keywords": ["айфон 16", "iphone 16"]}


class TestMatcherPipeline:
    def test_confirmed_buy(self):
        result = match_message("куплю айфон 16", [IPHONE])
        assert result.matched
        assert result.level == "confirmed"

    def test_sell_reject(self):
        result = match_message("продаю айфон 16", [IPHONE])
        assert not result.matched
        assert result.reject_reason == "sell_intent"

    def test_discussion_precise(self):
        result = match_message("у меня айфон 16 тормозит", [IPHONE], sensitivity="precise")
        assert not result.matched
        assert result.reject_reason == "discussion"
