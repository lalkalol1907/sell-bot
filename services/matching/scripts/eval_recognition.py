#!/usr/bin/env python3
"""Evaluate recognition quality on golden suite."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.recognition_harness import assert_case, load_cases, run_case

DEFAULT_BASELINE = ROOT / "reports" / "recognition_baseline.json"


def evaluate(cases_path: Path, *, semantic_only: bool = False) -> dict:
    cases = load_cases(cases_path)
    if semantic_only:
        cases = [c for c in cases if c.nlp_v2_semantic]
    else:
        cases = [c for c in cases if not c.nlp_v2_semantic]

    buy_tp = buy_fn = 0
    matched_tp = matched_fp = 0
    sell_fp = 0
    discussion_fp_precise = discussion_total_precise = 0
    failures = []

    for case in cases:
        actual = run_case(case)
        errors = assert_case(case, actual)
        if errors:
            failures.append({"id": case.id, "errors": errors, "actual": actual})

        is_buy_case = case.id.startswith(("explicit_buy", "implicit_buy", "semantic_", "fuzzy_", "multi_"))
        if is_buy_case and case.expect.matched:
            buy_tp += 1 if actual["matched"] else 0
            buy_fn += 0 if actual["matched"] else 1

        if actual["matched"]:
            matched_tp += 1
            if case.expect.matched is False:
                matched_fp += 1
        elif case.expect.matched:
            matched_fp += 0

        if case.id.startswith("sell_") and actual["matched"]:
            sell_fp += 1

        if case.id.startswith("discussion_") and case.sensitivity == "precise":
            discussion_total_precise += 1
            if actual["matched"]:
                discussion_fp_precise += 1

    recall = buy_tp / (buy_tp + buy_fn) if (buy_tp + buy_fn) else 1.0
    precision = matched_tp / (matched_tp + matched_fp) if (matched_tp + matched_fp) else 1.0
    discussion_fp_rate = (
        discussion_fp_precise / discussion_total_precise if discussion_total_precise else 0.0
    )

    return {
        "cases": len(cases),
        "recall_buy": recall,
        "precision_matched": precision,
        "sell_false_positives": sell_fp,
        "discussion_fp_precise": discussion_fp_rate,
        "failures": failures,
        "passed": len(failures) == 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=ROOT / "data" / "recognition_cases.yaml")
    parser.add_argument("--report", type=Path, default=ROOT / "reports" / "recognition_eval.json")
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--min-recall", type=float, default=0.85)
    parser.add_argument("--min-precision", type=float, default=0.70)
    parser.add_argument("--max-discussion-fp", type=float, default=0.10)
    parser.add_argument("--semantic", action="store_true")
    args = parser.parse_args()

    report = evaluate(args.cases, semantic_only=args.semantic)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    ok = True
    if report["recall_buy"] < args.min_recall:
        print(f"FAIL recall {report['recall_buy']:.3f} < {args.min_recall}")
        ok = False
    if report["precision_matched"] < args.min_precision:
        print(f"FAIL precision {report['precision_matched']:.3f} < {args.min_precision}")
        ok = False
    if report["sell_false_positives"] > 0:
        print(f"FAIL sell false positives: {report['sell_false_positives']}")
        ok = False
    if report["discussion_fp_precise"] > args.max_discussion_fp:
        print(f"FAIL discussion FP {report['discussion_fp_precise']:.3f}")
        ok = False
    if not report["passed"]:
        print(f"FAIL {len(report['failures'])} golden case mismatches")
        ok = False

    if args.baseline.is_file():
        baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
        for key in ("recall_buy", "precision_matched"):
            if key in baseline and report[key] < baseline[key] - 0.02:
                print(f"FAIL regression {key}: {report[key]:.3f} vs baseline {baseline[key]:.3f}")
                ok = False

    print(json.dumps({k: v for k, v in report.items() if k != "failures"}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
