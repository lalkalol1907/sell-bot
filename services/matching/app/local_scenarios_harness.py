"""Loader and runner for local user scenario dataset (not run in CI)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from app.config import fuzzy_min_score
from app.nlp.normalize import normalize_keyword
from app.nlp.product_gate import match_product
from app.pipeline.orchestrator import match_message
from app.paths import data_dir

SCENARIOS_PATH = data_dir() / "local_user_scenarios.yaml"

INTENT_ONLY_LINES = frozenset({
    "куплю", "купить", "ищу", "искать", "нужен", "нужна", "нужно", "хочу", "хотеть",
    "беру", "брать", "возьму", "взять", "приобрести", "приобрету", "заказать",
    "интересует", "интересовать", "достать", "предложите", "подскажите", "помогите",
    "подскажи", "помоги",
})


@dataclass
class ScenarioExpect:
    matched: bool | None = None
    product_id: int | None = None
    product_ids: list[int] | None = None
    segments: list[str] | None = None
    product_only: bool = False
    intent_class: str | None = None
    reject_reason: str | None = None
    level: str | None = None


@dataclass
class LocalScenario:
    id: str
    text: str
    products: list[dict] = field(default_factory=list)
    sensitivity: str = "precise"
    seller_id: int = 0
    expect: ScenarioExpect = field(default_factory=ScenarioExpect)


def _is_intent_only_line(line: str) -> bool:
    normalized = normalize_keyword(line)
    if not normalized:
        return True
    tokens = normalized.split()
    if len(tokens) == 1 and tokens[0] in INTENT_ONLY_LINES:
        return True
    if all(token in INTENT_ONLY_LINES for token in tokens):
        return True
    return False


def split_message_segments(text: str) -> list[str]:
    """Split multi-line / semicolon messages; skip lines that are only buy-intent."""
    chunks = re.split(r"[\n;]+", text)
    segments: list[str] = []
    for chunk in chunks:
        line = chunk.strip()
        if not line or _is_intent_only_line(line):
            continue
        segments.append(line)
    return segments


def resolve_segments(scenario: LocalScenario) -> list[str]:
    if scenario.expect.segments:
        return list(scenario.expect.segments)
    return split_message_segments(scenario.text)


def _match_segment_product_id(segment: str, products: list[dict]) -> int | None:
    hit = match_product(segment, products)
    if hit is None or hit.product_score < fuzzy_min_score():
        return None
    return hit.product_id


def load_local_dataset(path: Path | None = None) -> tuple[list[dict], list[LocalScenario]]:
    path = path or SCENARIOS_PATH
    with path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    catalog = raw.get("catalog") or []
    scenarios_raw = raw.get("scenarios") or []

    scenarios: list[LocalScenario] = []
    for item in scenarios_raw:
        expect_raw = item.get("expect") or {}
        scenarios.append(
            LocalScenario(
                id=item["id"],
                text=item["text"],
                products=catalog,
                sensitivity=item.get("sensitivity", "precise"),
                seller_id=item.get("seller_id", 0),
                expect=ScenarioExpect(
                    **{k: v for k, v in expect_raw.items() if k in ScenarioExpect.__dataclass_fields__}
                ),
            )
        )

    return catalog, scenarios


def run_scenario(scenario: LocalScenario) -> dict[str, Any]:
    segments = resolve_segments(scenario)
    segment_ids = [_match_segment_product_id(seg, scenario.products) for seg in segments]

    is_multi = (
        scenario.expect.segments is not None
        or scenario.expect.product_ids is not None
        or len(segments) > 1
    )
    product_only = scenario.expect.product_only

    if is_multi or product_only:
        full = match_message(
            scenario.text,
            scenario.products,
            sensitivity=scenario.sensitivity,
            seller_id=scenario.seller_id,
        )
        product_matched = bool(segments) and all(pid is not None for pid in segment_ids)
        return {
            "matched": product_matched,
            "level": full.level,
            "product_id": segment_ids[0] if segment_ids else None,
            "product_ids": segment_ids,
            "segments": segments,
            "intent_class": full.intent_class,
            "reject_reason": full.reject_reason,
            "product_score": full.product_score,
            "combined_score": full.score,
            "intent_score": full.intent,
            "product_matched": product_matched,
        }

    result = match_message(
        scenario.text,
        scenario.products,
        sensitivity=scenario.sensitivity,
        seller_id=scenario.seller_id,
    )
    return {
        "matched": result.matched,
        "level": result.level,
        "product_id": result.product.product_id if result.product else None,
        "product_ids": [result.product.product_id] if result.product else [],
        "segments": segments,
        "intent_class": result.intent_class,
        "reject_reason": result.reject_reason,
        "product_score": result.product_score,
        "combined_score": result.score,
        "intent_score": result.intent,
        "product_matched": result.product is not None,
    }


def assert_scenario(scenario: LocalScenario, actual: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    exp = scenario.expect

    if exp.matched is not None and actual["matched"] != exp.matched:
        errors.append(f"matched: expected {exp.matched}, got {actual['matched']}")

    if exp.product_ids is not None:
        actual_ids = actual.get("product_ids") or []
        if actual_ids != exp.product_ids:
            errors.append(f"product_ids: expected {exp.product_ids}, got {actual_ids}")
            if actual.get("segments"):
                for seg, pid in zip(actual["segments"], actual_ids, strict=False):
                    errors.append(f"  segment {seg!r} -> {pid}")

    if exp.product_id is not None and exp.product_ids is None:
        if actual.get("product_id") != exp.product_id:
            errors.append(f"product_id: expected {exp.product_id}, got {actual.get('product_id')}")

    if exp.intent_class is not None and actual.get("intent_class") != exp.intent_class:
        errors.append(f"intent_class: expected {exp.intent_class!r}, got {actual.get('intent_class')!r}")

    if exp.reject_reason is not None and actual.get("reject_reason") != exp.reject_reason:
        errors.append(f"reject_reason: expected {exp.reject_reason!r}, got {actual.get('reject_reason')!r}")

    if exp.level is not None and actual.get("level") != exp.level:
        errors.append(f"level: expected {exp.level!r}, got {actual.get('level')!r}")

    return errors
