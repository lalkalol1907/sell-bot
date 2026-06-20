"""Text normalization v2: emoji strip, translit, lemmatization."""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "]+",
    flags=re.UNICODE,
)

_TRANSLIT_PATH = Path(__file__).with_name("translit.json")
_MORPH = None


@lru_cache(maxsize=1)
def _translit_pairs() -> dict[str, str]:
    if _TRANSLIT_PATH.is_file():
        with _TRANSLIT_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    from importlib.resources import files

    return json.loads(files("app.nlp").joinpath("translit.json").read_text(encoding="utf-8"))


def _get_morph():
    global _MORPH
    if _MORPH is None:
        import pymorphy3

        _MORPH = pymorphy3.MorphAnalyzer()
    return _MORPH


def _sanitize(text: str) -> str:
    text = text.lower().strip()
    text = EMOJI_RE.sub(" ", text)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[^\w\sа-яё?]", " ", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def translit_expand(text: str) -> str:
    pairs = _translit_pairs()
    result = text
    for a, b in pairs.items():
        if a in result and b not in result:
            result = f"{result} {b}"
    return result


def _lemmatize_token(token: str) -> str:
    if not token or not re.search(r"[а-яё]", token, re.IGNORECASE):
        return token
    if re.search(r"[a-z0-9]", token):
        return token
    morph = _get_morph()
    parsed = morph.parse(token)
    if not parsed:
        return token
    best = parsed[0]
    if best.score < 0.4 or "UNKN" in best.tag:
        return token
    if "VERB" not in best.tag and "INFN" not in best.tag and "ADJF" not in best.tag:
        return token
    return best.normal_form


def normalize_text_v2(text: str, *, lemmatize: bool = True) -> str:
    text = _sanitize(text)
    text = translit_expand(text)

    if not lemmatize or not text:
        return text

    try:
        from razdel import tokenize

        tokens = [t.text for t in tokenize(text)]
        lemmas = [_lemmatize_token(t) for t in tokens]
        return " ".join(lemmas).strip()
    except Exception:
        return text


def normalize_keyword(text: str) -> str:
    """Normalize catalog keyword without translit expansion (avoids false negatives)."""
    return _sanitize(text)


def keyword_in_text(keyword: str, normalized_text: str) -> bool:
    kw = normalize_keyword(keyword)
    if not kw:
        return False
    if kw in normalized_text:
        return True
    parts = [p for p in kw.split() if len(p) > 1 or p.isdigit()]
    return bool(parts) and all(p in normalized_text for p in parts)


def normalize_text(text: str) -> str:
    return normalize_text_v2(text)
