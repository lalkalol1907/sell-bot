"""CLI entry points: make train / make publish."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def _run_pytest_fast() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_intent_dataset.py",
            "tests/test_product_pairs_dataset.py",
            "tests/test_recognition_golden.py",
            "-q",
            "-m",
            "not integration",
        ],
        cwd=ROOT,
    )
    if result.returncode != 0:
        raise RuntimeError("fast test suite failed during train")


def cmd_train() -> int:
    from app.training.calibrate import calibrate
    from app.training.datasets import generate_datasets
    from app.training.intent import train_intent

    print("==> regenerate datasets")
    generate_datasets()

    print("==> calibrate semantic thresholds")
    thresholds_path = calibrate()
    print(f"    wrote {thresholds_path}")

    print("==> train intent classifier")
    model_path = train_intent()
    print(f"    wrote {model_path}")

    print("==> run fast test suite")
    _run_pytest_fast()

    today = date.today().strftime("%Y.%m.%d")
    print("")
    print("Training complete. Publish with:")
    print(f"  make publish MODELS_VERSION={today}-1")
    return 0


def cmd_publish(version: str, *, max_drift: float = 0.02, no_latest: bool = False) -> int:
    from app.training.bundle import publish

    publish(version, max_drift=max_drift, update_latest=not no_latest)
    return 0


def main(argv: list[str] | None = None) -> int:
    from app.env import load_project_env

    load_project_env()

    parser = argparse.ArgumentParser(prog="python -m app.training.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("train", help="Regenerate datasets, calibrate, train intent, run fast tests")

    pub = sub.add_parser("publish", help="Validate, parity-check, golden gate, upload to S3")
    pub.add_argument("--version", required=True)
    pub.add_argument("--max-drift", type=float, default=0.02)
    pub.add_argument("--no-latest", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "train":
        return cmd_train()
    if args.command == "publish":
        return cmd_publish(args.version, max_drift=args.max_drift, no_latest=args.no_latest)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
