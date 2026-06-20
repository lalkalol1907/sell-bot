"""Generate intent training/eval datasets from YAML seed files in data/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from app.paths import data_dir

DATA = data_dir()
INTENT_SAMPLES_PATH = DATA / "intent_samples.yaml"
PRODUCT_KEYWORDS_PATH = DATA / "product_catalog_keywords.yaml"
PRODUCT_PAIRS_SEED_PATH = DATA / "product_pairs_seed.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_intent_samples(path: Path | None = None) -> dict[str, Any]:
    path = path or INTENT_SAMPLES_PATH
    raw = _load_yaml(path)
    return {
        "buy": list(raw.get("buy") or []),
        "sell": list(raw.get("sell") or []),
        "discussion": list(raw.get("discussion") or []),
        "none": list(raw.get("none") or []),
        "variant_buy": list(raw.get("variant_buy") or []),
        "variant_sell": list(raw.get("variant_sell") or []),
        "variant_discussion": list(raw.get("variant_discussion") or []),
        "variant_none_color": list(raw.get("variant_none_color") or []),
        "eval_slices": dict(raw.get("eval_slices") or {}),
    }


def load_product_catalog_keywords(path: Path | None = None) -> dict[str, list[str]]:
    path = path or PRODUCT_KEYWORDS_PATH
    raw = _load_yaml(path)
    return {str(title): list(keywords) for title, keywords in raw.items()}


def load_product_pairs_seed(path: Path | None = None) -> tuple[set[str], list[dict[str, Any]]]:
    path = path or PRODUCT_PAIRS_SEED_PATH
    raw = _load_yaml(path)
    variant_messages = set(raw.get("variant_pair_messages") or [])
    pairs = list(raw.get("pairs") or [])
    return variant_messages, pairs


def _pair_row(
    item: dict[str, Any],
    keywords: dict[str, list[str]],
    variant_messages: set[str],
) -> dict[str, Any]:
    message = item["message"]
    title = item["product_title"]
    match = int(item["match"])
    storage_gb = item.get("storage_gb")
    color = item.get("color")

    row: dict[str, Any] = {
        "message": message,
        "product_title": title,
        "match": match,
        "keywords": keywords.get(title, [title.lower()]),
    }
    if storage_gb is not None:
        row["storage_gb"] = storage_gb
    if color is not None:
        row["color"] = color
    if message in variant_messages or storage_gb is not None or color is not None:
        row["eval_scope"] = "variant"
    else:
        row["eval_scope"] = "skip"
    return row


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def generate_datasets() -> None:
    """Regenerate intent and product-pairs JSONL from data/*.yaml seeds."""
    main()


def main() -> None:
    samples = load_intent_samples()
    keywords = load_product_catalog_keywords()
    variant_messages, pair_items = load_product_pairs_seed()

    slices = samples["eval_slices"]
    buy = samples["buy"] + samples["variant_buy"]
    sell = samples["sell"] + samples["variant_sell"]
    discussion = samples["discussion"] + samples["variant_discussion"]
    none = samples["none"] + samples["variant_none_color"]

    train_rows: list[dict[str, str]] = []
    for label, texts in (
        ("buy", buy),
        ("sell", sell),
        ("discussion", discussion),
        ("none", none),
    ):
        for text in texts:
            train_rows.append({"text": text, "label": label})

    eval_rows: list[dict[str, str]] = []
    eval_buy = (
        samples["buy"][:slices.get("buy", 12)]
        + samples["variant_buy"][:slices.get("variant_buy", 8)]
    )
    eval_sell = (
        samples["sell"][:slices.get("sell", 12)]
        + samples["variant_sell"][:slices.get("variant_sell", 8)]
    )
    eval_discussion = (
        samples["discussion"][:slices.get("discussion", 12)]
        + samples["variant_discussion"][:slices.get("variant_discussion", 8)]
    )
    eval_none = (
        samples["none"][:slices.get("none", 12)]
        + samples["variant_none_color"][:slices.get("variant_none_color", 8)]
    )
    for text in eval_buy:
        eval_rows.append({"text": text, "label": "buy"})
    for text in eval_sell:
        eval_rows.append({"text": text, "label": "sell"})
    for text in eval_discussion:
        eval_rows.append({"text": text, "label": "discussion"})
    for text in eval_none:
        eval_rows.append({"text": text, "label": "none"})

    pair_rows = [_pair_row(item, keywords, variant_messages) for item in pair_items]

    write_jsonl(DATA / "intent_train.jsonl", train_rows)
    write_jsonl(DATA / "intent_eval.jsonl", eval_rows)
    write_jsonl(DATA / "product_pairs_eval.jsonl", pair_rows)
    print(f"train={len(train_rows)} eval={len(eval_rows)} pairs={len(pair_rows)}")


if __name__ == "__main__":
    main()
