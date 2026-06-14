import pytest

from app.intent import intent_score
from app.normalize import normalize_text, translit_pairs


class TestNormalizeText:
    def test_lowercase_and_strip(self):
        assert normalize_text("  КУПЛЮ  ") == "куплю"

    def test_emoji_removed(self):
        result = normalize_text("куплю 🔥 айфон")
        assert "🔥" not in result
        assert "куплю" in result

    def test_iphone_translit(self):
        assert "айфон" in normalize_text("Куплю iPhone 16")

    def test_empty_string(self):
        assert normalize_text("") == ""

    def test_punctuation_collapsed(self):
        result = normalize_text("куплю!!!  айфон???")
        assert "куплю" in result
        assert "айфон" in result


class TestTranslitPairs:
    def test_adds_ayfon_when_iphone_present(self):
        assert "айфон" in translit_pairs("iphone 16")

    def test_adds_iphone_when_ayfon_present(self):
        assert "iphone" in translit_pairs("айфон 16")

    def test_no_duplicate_when_both_present(self):
        text = "iphone айфон 16"
        assert translit_pairs(text).count("iphone") == 1
        assert translit_pairs(text).count("айфон") == 1


class TestIntentScore:
    def test_positive_buy_intent(self):
        assert intent_score("куплю айфон") == 0.9

    def test_negative_sell_intent(self):
        assert intent_score("продаю айфон") == -1.0

    def test_indirect_question(self):
        assert intent_score("кто знает где найти") == 0.55

    def test_question_mark(self):
        assert intent_score("есть айфон?") == 0.55

    def test_neutral_text(self):
        assert intent_score("просто текст про телефон") == 0.1

    def test_sell_phrase_in_tokens(self):
        assert intent_score("в наличии айфон") == -1.0
