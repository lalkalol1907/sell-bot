"""Golden recognition case loader and runner."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from app.pipeline.orchestrator import match_message
from app.paths import data_dir

CASES_PATH = data_dir() / "recognition_cases.yaml"


@dataclass
class CaseExpect:
    matched: bool | None = None
    level: str | None = None
    product_id: int | None = None
    intent_class: str | None = None
    reject_reason: str | None = None
    min_product_score: float | None = None
    min_semantic_score: float | None = None


@dataclass
class RecognitionCase:
    id: str
    text: str
    products: list[dict] = field(default_factory=list)
    sensitivity: str = "precise"
    seller_id: int = 1
    requires_semantic: bool = False
    expect: CaseExpect = field(default_factory=CaseExpect)


def load_cases(path: Path | None = None) -> list[RecognitionCase]:
    path = path or CASES_PATH
    with path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f) or []

    cases: list[RecognitionCase] = []
    for item in raw:
        expect_raw = item.get("expect") or {}
        requires_semantic = bool(
            item.get("requires_semantic")
            or item.get("nlp_v2_semantic")
        )
        cases.append(
            RecognitionCase(
                id=item["id"],
                text=item["text"],
                products=item.get("products") or [],
                sensitivity=item.get("sensitivity", "precise"),
                seller_id=item.get("seller_id", 1),
                requires_semantic=requires_semantic,
                expect=CaseExpect(**{k: v for k, v in expect_raw.items() if k in CaseExpect.__dataclass_fields__}),
            )
        )
    return cases


def run_case(case: RecognitionCase) -> dict[str, Any]:
    result = match_message(
        case.text,
        case.products,
        sensitivity=case.sensitivity,
        seller_id=case.seller_id,
    )
    return {
        "matched": result.matched,
        "level": result.level,
        "product_id": result.product.product_id if result.product else None,
        "intent_class": result.intent_class,
        "reject_reason": result.reject_reason,
        "product_score": result.product_score,
        "semantic_score": result.product.semantic_score if result.product else 0.0,
        "intent_score": result.intent,
        "combined_score": result.score,
    }


def assert_case(case: RecognitionCase, actual: dict[str, Any], *, score_tolerance: float = 0.05) -> list[str]:
    errors: list[str] = []
    exp = case.expect

    if exp.matched is not None and actual["matched"] != exp.matched:
        errors.append(f"matched: expected {exp.matched}, got {actual['matched']}")

    if exp.level is not None and actual.get("level") != exp.level:
        errors.append(f"level: expected {exp.level!r}, got {actual.get('level')!r}")

    if exp.product_id is not None and actual.get("product_id") != exp.product_id:
        errors.append(f"product_id: expected {exp.product_id}, got {actual.get('product_id')}")

    if exp.intent_class is not None and actual.get("intent_class") != exp.intent_class:
        errors.append(f"intent_class: expected {exp.intent_class!r}, got {actual.get('intent_class')!r}")

    if exp.reject_reason is not None and actual.get("reject_reason") != exp.reject_reason:
        errors.append(f"reject_reason: expected {exp.reject_reason!r}, got {actual.get('reject_reason')!r}")

    if exp.min_product_score is not None:
        score = actual.get("product_score") or 0.0
        if score < exp.min_product_score - score_tolerance:
            errors.append(f"product_score {score} < {exp.min_product_score}")

    if exp.min_semantic_score is not None:
        score = actual.get("semantic_score") or 0.0
        if score < exp.min_semantic_score - score_tolerance:
            errors.append(f"semantic_score {score} < {exp.min_semantic_score}")

    return errors
