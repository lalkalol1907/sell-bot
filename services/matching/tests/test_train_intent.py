"""Train intent model smoke test."""

from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parent.parent


def test_train_intent_mini(tmp_path, monkeypatch):
    train = tmp_path / "train.jsonl"
    eval_path = tmp_path / "eval.jsonl"
    rows = [
        '{"text": "куплю айфон", "label": "buy"}',
        '{"text": "продаю айфон", "label": "sell"}',
        '{"text": "у меня айфон тормозит", "label": "discussion"}',
        '{"text": "привет всем", "label": "none"}',
    ]
    train.write_text("\n".join(rows * 6), encoding="utf-8")
    eval_path.write_text("\n".join(rows), encoding="utf-8")

    import subprocess
    import sys

    out = tmp_path / "model.joblib"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "train_intent.py"),
            "--train",
            str(train),
            "--eval",
            str(eval_path),
            "--output",
            str(out),
            "--no-embeddings",
            "--min-macro-f1",
            "0.0",
            "--min-discussion-recall",
            "0.0",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert out.is_file()
