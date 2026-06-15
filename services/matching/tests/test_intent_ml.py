"""Intent classifier ML path tests."""

from pathlib import Path

import joblib
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


@pytest.fixture
def tiny_model(tmp_path, monkeypatch, reload_modules):
    vectorizer = TfidfVectorizer()
    x = vectorizer.fit_transform(["куплю айфон", "продаю айфон", "тормозит айфон", "привет"])
    clf = LogisticRegression()
    clf.fit(x, ["buy", "sell", "discussion", "none"])

    path = tmp_path / "intent_test.joblib"
    joblib.dump({"classifier": clf, "vectorizer": vectorizer, "scaler": None, "feature_type": "tfidf"}, path)

    monkeypatch.setenv("NLP_V2_INTENT_ML", "true")
    monkeypatch.setenv("INTENT_MODEL_PATH", str(path))
    reload_modules()
    from app.nlp.intent_classifier import reset_model_cache

    reset_model_cache()
    return path


def test_ml_classifier_buy(tiny_model, reload_modules):
    from app.nlp.intent_classifier import classify_intent

    result = classify_intent("куплю айфон 16")
    assert result.label == "buy"


def test_ml_classifier_fallback_on_error(tiny_model, monkeypatch, reload_modules):
    monkeypatch.setenv("INTENT_MODEL_PATH", "/nonexistent/model.joblib")
    reload_modules()
    from app.nlp.intent_classifier import classify_intent, reset_model_cache

    reset_model_cache()
    result = classify_intent("продаю айфон")
    assert result.label == "sell"
