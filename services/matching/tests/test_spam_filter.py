from app.spam_filter import check_spam, is_spam_by_length, matches_learned_spam


class TestSpamFilter:
    def test_rejects_short_message(self):
        assert is_spam_by_length("куплю") is True

    def test_accepts_normal_length(self):
        assert is_spam_by_length("куплю айфон 16") is False

    def test_rejects_too_long(self):
        assert is_spam_by_length("x" * 2001) is True

    def test_learned_phrase_blocks(self):
        assert matches_learned_spam("продам курс по заработку", ["курс по заработку"]) is True

    def test_check_spam_length_reason(self):
        assert check_spam("ok", []) == "length"

    def test_check_spam_learned_reason(self):
        assert check_spam("хочу курс по заработку срочно", ["курс по заработку"]) == "learned"
