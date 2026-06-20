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

    from app.training.intent import train_intent

    out = tmp_path / "intent.joblib"
    train_intent(
        train_path=train,
        eval_path=eval_path,
        output_path=out,
        use_embeddings=False,
        min_macro_f1=0.0,
        min_discussion_recall=0.0,
    )
    assert out.is_file()
