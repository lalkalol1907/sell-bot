"""Unit tests for normalize v2."""


class TestNormalizeV2:
    def test_lemmatize_kuplyu(self, reload_modules):
        from app.nlp.normalize import normalize_text

        result = normalize_text("куплю айфон")
        assert "купить" in result
        assert "айфон" in result

    def test_translit_iphone(self, reload_modules):
        from app.nlp.normalize import normalize_text

        result = normalize_text("Куплю iPhone 16")
        assert "айфон" in result
        assert "iphone" in result

    def test_emoji_removed(self, reload_modules):
        from app.nlp.normalize import normalize_text

        result = normalize_text("куплю 🔥 айфон")
        assert "🔥" not in result

    def test_empty(self, reload_modules):
        from app.nlp.normalize import normalize_text

        assert normalize_text("") == ""

    def test_samsung_translit(self, reload_modules):
        from app.nlp.normalize import translit_expand

        assert "samsung" in translit_expand("самсунг s24") or "самсунг" in translit_expand("samsung s24")

    def test_keeps_loanword_galaxy(self, reload_modules):
        from app.nlp.normalize import normalize_text

        result = normalize_text("где взять галакси эс 24")
        assert "галакси" in result
        assert "галаксить" not in result
