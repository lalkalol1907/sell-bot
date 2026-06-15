"""Storage and color extraction + variant-aware score adjustment."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.config import (
    VARIANT_COLOR_MISMATCH_MULT,
    VARIANT_COLOR_MISSING_MULT,
    VARIANT_STORAGE_MISMATCH_MULT,
    VARIANT_STORAGE_MISSING_MULT,
)
from app.nlp.normalize import normalize_keyword

STORAGE_GB_RE = re.compile(
    r"\b(\d{2,4})\s*(?:gb|гб|g)\b",
    re.IGNORECASE,
)
STORAGE_TB_RE = re.compile(
    r"\b(\d)\s*(?:tb|тб)\b",
    re.IGNORECASE,
)
STORAGE_STANDALONE_RE = re.compile(r"\b(64|128|256|512|1024|2048)\b")

COLOR_ALIASES: dict[str, str] = {
    "black": "black",
    "черный": "black",
    "чёрный": "black",
    "white": "white",
    "белый": "white",
    "blue": "blue",
    "синий": "blue",
    "голубой": "blue",
    "green": "green",
    "зеленый": "green",
    "зелёный": "green",
    "red": "red",
    "красный": "red",
    "pink": "pink",
    "розовый": "pink",
    "purple": "purple",
    "фиолетовый": "purple",
    "gold": "gold",
    "золотой": "gold",
    "золото": "gold",
    "silver": "silver",
    "серебристый": "silver",
    "серебро": "silver",
    "gray": "gray",
    "grey": "gray",
    "серый": "gray",
    "orange": "orange",
    "оранжевый": "orange",
    "yellow": "yellow",
    "желтый": "yellow",
    "жёлтый": "yellow",
    "natural": "natural",
    "натуральный": "natural",
    "titanium": "titanium",
    "титан": "titanium",
    "титановый": "titanium",
    "desert": "desert",
    "пустынный": "desert",
    "graphite": "graphite",
    "графит": "graphite",
    "midnight": "midnight",
    "полночь": "midnight",
    "starlight": "starlight",
    "сияние": "starlight",
    "lavender": "lavender",
    "лаванда": "lavender",
    "лиловый": "lavender",
}

COLOR_PHRASES = [
    ("desert titanium", "desert"),
    ("natural titanium", "natural"),
    ("black titanium", "black"),
    ("white titanium", "white"),
    ("blue titanium", "blue"),
    ("пустынный титан", "desert"),
    ("натуральный титан", "natural"),
    ("черный титан", "black"),
    ("чёрный титан", "black"),
    ("белый титан", "white"),
    ("синий титан", "blue"),
]


@dataclass(frozen=True)
class VariantAttrs:
    storage_gb: int | None = None
    color: str | None = None


def _normalize_storage_gb(value: int) -> int:
    if value >= 1000 and value % 1024 == 0:
        return value
    return value


def extract_storage_gb(text: str) -> int | None:
    normalized = normalize_keyword(text)
    if not normalized:
        return None

    for match in STORAGE_TB_RE.finditer(normalized):
        return int(match.group(1)) * 1024

    for match in STORAGE_GB_RE.finditer(normalized):
        return _normalize_storage_gb(int(match.group(1)))

    for match in STORAGE_STANDALONE_RE.finditer(normalized):
        return int(match.group(1))

    return None


def extract_color(text: str) -> str | None:
    normalized = normalize_keyword(text)
    if not normalized:
        return None

    for phrase, canonical in sorted(COLOR_PHRASES, key=lambda x: -len(x[0])):
        if phrase in normalized:
            return canonical

    tokens = normalized.split()
    for token in tokens:
        if token in COLOR_ALIASES:
            return COLOR_ALIASES[token]

    return None


def extract_variant_attrs(text: str) -> VariantAttrs:
    return VariantAttrs(
        storage_gb=extract_storage_gb(text),
        color=extract_color(text),
    )


def _product_text(product: dict) -> str:
    parts = [product.get("title", "")]
    parts.extend(product.get("keywords") or [])
    if product.get("storage_gb") is not None:
        parts.append(f"{product['storage_gb']}gb")
    if product.get("color"):
        parts.append(str(product["color"]))
    return " ".join(str(p) for p in parts if p)


def extract_product_variant(product: dict) -> VariantAttrs:
    explicit_storage = product.get("storage_gb")
    explicit_color = product.get("color")

    text = _product_text(product)
    return VariantAttrs(
        storage_gb=int(explicit_storage) if explicit_storage is not None else extract_storage_gb(text),
        color=str(explicit_color).lower() if explicit_color else extract_color(text),
    )


def variant_score_multiplier(message_attrs: VariantAttrs, product_attrs: VariantAttrs) -> float:
    """Return multiplier in (0, 1]; 1.0 = full match, lower = penalized similarity."""
    multiplier = 1.0

    if message_attrs.storage_gb is not None:
        if product_attrs.storage_gb is None:
            multiplier *= VARIANT_STORAGE_MISSING_MULT
        elif message_attrs.storage_gb != product_attrs.storage_gb:
            multiplier *= VARIANT_STORAGE_MISMATCH_MULT

    if message_attrs.color is not None:
        if product_attrs.color is None:
            multiplier *= VARIANT_COLOR_MISSING_MULT
        elif message_attrs.color != product_attrs.color:
            multiplier *= VARIANT_COLOR_MISMATCH_MULT

    return multiplier


def apply_variant_adjustment(base_score: float, message_text: str, product: dict) -> float:
    if base_score <= 0:
        return base_score
    message_attrs = extract_variant_attrs(message_text)
    product_attrs = extract_product_variant(product)
    return base_score * variant_score_multiplier(message_attrs, product_attrs)
