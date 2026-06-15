from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

POSITIVE = {
    "купить", "куплю", "ищу", "нужен", "нужна", "нужно", "хотеть", "хочу",
    "почём", "почем", "сколько", "беру", "возьму", "приобрести", "приобрету",
    "заказать", "интересует", "достать",
}
NEGATIVE = {
    "продать", "продам", "продаю", "продавать", "продаёт", "продает", "отдать", "отдам", "отдаю", "отдавать",
    "наличие", "наличии", "опт", "оптом", "продажа", "реализую", "сдаю",
}
INDIRECT = {
    "кто", "где", "есть", "подскажите", "помогите", "достать", "срочно",
    "подскажи", "помоги", "возьмет", "возьмёт",
}
DISCUSSION_MARKERS = {
    "тормозит", "глючит", "сломался", "сломалась", "батарея", "экран",
    "обновление", "после", "проблема", "не работает", "разбился", "чехол",
    "пленка", "плёнка", "настроил", "настроила", "совет", "рекомендуете",
    "перегревается", "шумят", "мерцает", "вылетает", "зависает",
}

INTENT_SCORES = {
    "buy": 0.9,
    "sell": -1.0,
    "discussion": 0.1,
    "none": 0.1,
}


@dataclass
class IntentResult:
    label: str
    score: float


_classifier = None
_vectorizer = None
_scaler = None
_feature_type = "heuristic"


def _load_ml_model():
    global _classifier, _vectorizer, _scaler, _feature_type
    if _classifier is not None:
        return _classifier, _vectorizer, _scaler, _feature_type

    from app.config import INTENT_MODEL_PATH, NLP_V2_INTENT_ML

    if not NLP_V2_INTENT_ML:
        return None, None, None, "heuristic"

    path = Path(INTENT_MODEL_PATH)
    if not path.is_file():
        return None, None, None, "heuristic"

    import joblib

    bundle = joblib.load(path)
    _classifier = bundle.get("classifier")
    _vectorizer = bundle.get("vectorizer")
    _scaler = bundle.get("scaler")
    _feature_type = bundle.get("feature_type", "embeddings")
    return _classifier, _vectorizer, _scaler, _feature_type


def _build_features(text: str, vectorizer, feature_type: str):
    import numpy as np

    from app.nlp.normalize import normalize_text

    normalized = normalize_text(text)
    if feature_type == "tfidf" and vectorizer is not None:
        return vectorizer.transform([normalized])
    if feature_type == "embeddings":
        from app.embeddings.encoder import encode_text

        vec = np.array([encode_text(normalized)], dtype=np.float32)
        return vec
    return None


def intent_score_heuristic(text: str) -> IntentResult:
    tokens = set(text.split())

    strong_buy_phrases = (
        "ищу купить",
        "хочу купить",
        "буду купить",
        "нужно купить",
        "ищу куплю",
        "нет, ищу",
        "нет ищу",
    )
    if any(phrase in text for phrase in strong_buy_phrases):
        return IntentResult("buy", 0.9)

    if tokens & NEGATIVE or "в наличии" in text:
        return IntentResult("sell", -1.0)
    if any(marker in text for marker in ("не работает", "не включается", "не ловит", "не коннект")):
        return IntentResult("discussion", 0.1)
    discussion_hints = (
        "тормоз", "глюч", "сломал", "батар", "перегрев", "шум", "мерца", "вылет", "завис",
        "разбил", "чехол", "плёнк", "пленк", "совет", "рекоменд", "настроил",
    )
    if any(h in text for h in discussion_hints) and not (tokens & POSITIVE):
        return IntentResult("discussion", 0.1)
    if tokens & DISCUSSION_MARKERS and not (tokens & POSITIVE):
        return IntentResult("discussion", 0.1)
    if tokens & POSITIVE:
        return IntentResult("buy", 0.9)
    if "?" in text or (tokens & INDIRECT):
        return IntentResult("buy", 0.55)
    return IntentResult("none", 0.1)


def classify_intent(text: str) -> IntentResult:
    clf, vectorizer, scaler, feature_type = _load_ml_model()
    if clf is None:
        return intent_score_heuristic(text)

    try:
        import numpy as np

        features = _build_features(text, vectorizer, feature_type)
        if features is None:
            return intent_score_heuristic(text)
        if scaler is not None and feature_type == "embeddings":
            features = scaler.transform(features)
        label = str(clf.predict(features)[0])
        score = INTENT_SCORES.get(label, 0.1)
        return IntentResult(label, score)
    except Exception:
        return intent_score_heuristic(text)


def reset_model_cache() -> None:
    global _classifier, _vectorizer, _scaler, _feature_type
    _classifier = None
    _vectorizer = None
    _scaler = None
    _feature_type = "heuristic"
