from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

POSITIVE = {
    "купить", "куплю", "ищу", "искать", "нужен", "нужна", "нужно", "хотеть", "хочу",
    "почём", "почем", "сколько", "беру", "брать", "возьму", "взять", "приобрести", "приобрету",
    "заказать", "интересует", "интересовать", "достать",
}
NEGATIVE = {
    "продать", "продам", "продаю", "продавать", "продаёт", "продает", "отдать", "отдам", "отдаю", "отдавать",
    "наличие", "наличии", "опт", "оптом", "продажа", "реализую", "реализовать", "сдаю", "сдавать",
}
INDIRECT = {
    "кто", "где", "есть", "подскажите", "помогите", "достать", "срочно",
    "подскажи", "помоги", "возьмет", "возьмёт", "предложите", "предложи",
}

DISCUSSION_BROKEN_PHRASES = (
    "не работать", "не работает", "не включаться", "не ловить", "не коннект",
)
DISCUSSION_HINTS = (
    "тормоз", "тормозить", "глюч", "сломал", "батар", "перегрев", "шум", "мерца", "вылет", "завис",
    "разбил", "чехол", "плёнк", "пленк", "совет", "рекоменд", "настроить", "настроил",
)
DISCUSSION_TOKENS = {
    "тормозить", "глючить", "сломаться", "сломалась", "батарея", "экран",
    "обновление", "после", "проблема", "не работать", "разбиться", "чехол",
    "пленка", "плёнка", "настроить", "настроила", "совет", "рекомендовать",
    "перегреваться", "шуметь", "мерцать", "вылетать", "зависать",
}

PRODUCT_MARKERS = (
    "iphone", "айфон", "ipad", "айпад", "macbook", "макбук", "airpods", "эйрпод",
    "galaxy", "samsung", "самсунг", "яндекс", "homepod", "хоумпод", "watch",
    "pro max", "pro ", " air ", " станци", "airpods", "honor", "sony",
)
SPEC_TOKEN_RE = re.compile(
    r"\b(64|128|256|512|1024|2048|1tb|16|15|14|13|12)\b",
    re.IGNORECASE,
)

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

    from app.config import INTENT_MODEL_NAME
    from app.paths import models_dir

    default_path = str(models_dir() / INTENT_MODEL_NAME)
    path = Path(os.getenv("INTENT_MODEL_PATH", default_path))
    if not path.is_file():
        logger.warning("Intent ML model missing at %s, using heuristic fallback", path)
        return None, None, None, "heuristic"

    import joblib

    bundle = joblib.load(path)
    _classifier = bundle.get("classifier")
    _vectorizer = bundle.get("vectorizer")
    _scaler = bundle.get("scaler")
    _feature_type = bundle.get("feature_type", "embeddings")
    return _classifier, _vectorizer, _scaler, _feature_type


def _build_features(normalized: str, vectorizer, feature_type: str):
    import numpy as np

    if feature_type == "tfidf" and vectorizer is not None:
        return vectorizer.transform([normalized])
    if feature_type == "embeddings":
        from app.embeddings.encoder import encode_text

        vec = np.array([encode_text(normalized)], dtype=np.float32)
        return vec
    return None


def _looks_like_discussion(text: str, tokens: set[str]) -> bool:
    if tokens & POSITIVE:
        return False
    if any(phrase in text for phrase in DISCUSSION_BROKEN_PHRASES):
        return True
    if any(hint in text for hint in DISCUSSION_HINTS):
        return True
    return bool(tokens & DISCUSSION_TOKENS)


def _looks_like_product_listing(text: str) -> bool:
    """Short product line from chat (often without «куплю»)."""
    lower = text.lower()
    if not any(marker in lower for marker in PRODUCT_MARKERS):
        return False
    return bool(SPEC_TOKEN_RE.search(lower))


def _merge_with_heuristic(heuristic: IntentResult, ml: IntentResult) -> IntentResult:
    """Apply high-precision heuristic guardrails on top of ML output."""
    if heuristic.label == "sell":
        return heuristic

    if heuristic.label == "discussion":
        return heuristic

    # Явный buy (куплю/ищу…) не должен превращаться в sell из-за цветов/моделей в тексте.
    if heuristic.label == "buy" and ml.label == "sell":
        return heuristic

    if ml.label == "buy" and heuristic.label == "none":
        return heuristic

    # Indirect buy ("есть X?") — keep low confidence for precise sensitivity.
    if heuristic.label == "buy" and heuristic.score <= 0.55 and ml.label == "buy":
        return heuristic

    if ml.label in ("none", "discussion") and heuristic.label == "buy" and heuristic.score >= 0.55:
        return heuristic

    if ml.label in ("buy", "none") and heuristic.label == "discussion":
        return heuristic

    return ml


def intent_score_heuristic(text: str) -> IntentResult:
    tokens = set(text.split())

    strong_buy_phrases = (
        "ищу купить",
        "искать купить",
        "хочу купить",
        "буду купить",
        "нужно купить",
        "ищу куплю",
        "искать купить",
        "нет, ищу",
        "нет ищу",
    )
    if any(phrase in text for phrase in strong_buy_phrases):
        return IntentResult("buy", 0.9)

    if tokens & NEGATIVE or "в наличии" in text:
        return IntentResult("sell", -1.0)
    if _looks_like_discussion(text, tokens):
        return IntentResult("discussion", 0.1)
    if tokens & POSITIVE:
        return IntentResult("buy", 0.9)
    if _looks_like_product_listing(text):
        return IntentResult("buy", 0.55)
    if "?" in text or (tokens & INDIRECT):
        return IntentResult("buy", 0.55)
    return IntentResult("none", 0.1)


def classify_intent(text: str, *, normalized: str | None = None) -> IntentResult:
    if normalized is None:
        from app.nlp.normalize import normalize_text

        normalized = normalize_text(text)

    heuristic = intent_score_heuristic(normalized)

    clf, vectorizer, scaler, feature_type = _load_ml_model()
    if clf is None:
        return heuristic

    try:
        features = _build_features(normalized, vectorizer, feature_type)
        if features is None:
            return heuristic
        if scaler is not None and feature_type == "embeddings":
            features = scaler.transform(features)
        label = str(clf.predict(features)[0])
        score = INTENT_SCORES.get(label, 0.1)
        ml = IntentResult(label, score)
        return _merge_with_heuristic(heuristic, ml)
    except Exception as exc:
        logger.warning("Intent ML inference failed: %s", exc)
        return heuristic


def warmup_intent_model() -> None:
    """Load intent classifier and run a dummy inference."""
    clf, _, _, _ = _load_ml_model()
    if clf is None:
        logger.info("Intent ML model not configured, using heuristic only")
        return
    classify_intent("куплю warmup")


def reset_model_cache() -> None:
    global _classifier, _vectorizer, _scaler, _feature_type
    _classifier = None
    _vectorizer = None
    _scaler = None
    _feature_type = "heuristic"
