"""Backward-compatible intent re-exports."""

from app.nlp.intent_classifier import classify_intent, intent_score_heuristic

def intent_score(text: str) -> float:
    return intent_score_heuristic(text).score

__all__ = ["intent_score", "classify_intent", "intent_score_heuristic"]
