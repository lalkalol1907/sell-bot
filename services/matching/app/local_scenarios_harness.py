"""Loader and runner for local user scenario dataset (not run in CI)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from app.pipeline.orchestrator import match_message
from app.paths import data_dir

SCENARIOS_PATH = data_dir() / "local_user_scenarios.yaml"


@dataclass
class ScenarioExpect:
    matched: bool | None = None
    product_id: int | None = None
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
        "intent_class": result.intent_class,
        "reject_reason": result.reject_reason,
        "product_score": result.product_score,
        "combined_score": result.score,
        "intent_score": result.intent,
    }


def assert_scenario(scenario: LocalScenario, actual: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    exp = scenario.expect

    if exp.matched is not None and actual["matched"] != exp.matched:
        errors.append(f"matched: expected {exp.matched}, got {actual['matched']}")

    if exp.product_id is not None and actual.get("product_id") != exp.product_id:
        errors.append(f"product_id: expected {exp.product_id}, got {actual.get('product_id')}")

    if exp.intent_class is not None and actual.get("intent_class") != exp.intent_class:
        errors.append(f"intent_class: expected {exp.intent_class!r}, got {actual.get('intent_class')!r}")

    if exp.reject_reason is not None and actual.get("reject_reason") != exp.reject_reason:
        errors.append(f"reject_reason: expected {exp.reject_reason!r}, got {actual.get('reject_reason')!r}")

    if exp.level is not None and actual.get("level") != exp.level:
        errors.append(f"level: expected {exp.level!r}, got {actual.get('level')!r}")

    return errors
