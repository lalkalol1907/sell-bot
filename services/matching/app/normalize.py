import re
import unicodedata

EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "]+",
    flags=re.UNICODE,
)


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = EMOJI_RE.sub(" ", text)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[^\w\sа-яё?]", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return translit_pairs(text)


def translit_pairs(text: str) -> str:
    pairs = [("iphone", "айфон"), ("айфон", "iphone")]
    result = text
    for a, b in pairs:
        if a in result and b not in result:
            result = f"{result} {b}"
    return result
