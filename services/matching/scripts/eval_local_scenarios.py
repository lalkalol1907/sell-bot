#!/usr/bin/env python3
"""Evaluate local user scenarios against the matching pipeline.

Usage (from services/matching):
    python scripts/eval_local_scenarios.py
    python scripts/eval_local_scenarios.py --only-failures
    python scripts/eval_local_scenarios.py --id iphone_pmax_desert_ru_spaces
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.local_scenarios_harness import (
    assert_scenario,
    load_local_dataset,
    run_scenario,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate local user scenario dataset")
    parser.add_argument("--only-failures", action="store_true", help="Show only failing cases")
    parser.add_argument("--id", dest="case_id", help="Run a single scenario by id")
    args = parser.parse_args()

    catalog, scenarios = load_local_dataset()
    if args.case_id:
        scenarios = [s for s in scenarios if s.id == args.case_id]
        if not scenarios:
            print(f"Scenario not found: {args.case_id}")
            return 1

    passed = 0
    failed = 0

    print(f"Catalog: {len(catalog)} products, scenarios: {len(scenarios)}")
    print()

    for scenario in scenarios:
        actual = run_scenario(scenario)
        errors = assert_scenario(scenario, actual)
        ok = not errors

        if ok:
            passed += 1
            if not args.only_failures:
                print(f"  OK  {scenario.id}")
        else:
            failed += 1
            print(f"FAIL  {scenario.id}")
            print(f"      text: {scenario.text}")
            for err in errors:
                print(f"      {err}")
            print(
                f"      actual: matched={actual['matched']} "
                f"product_id={actual['product_id']} "
                f"product_ids={actual.get('product_ids')} "
                f"intent={actual['intent_class']!r} "
                f"reject={actual['reject_reason']!r} "
                f"product_score={actual['product_score']:.3f}"
            )
            print()

    print(f"\nResult: {passed} passed, {failed} failed, {len(scenarios)} total")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
