#!/usr/bin/env python3
"""Train intent classifier head on frozen embeddings."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MODELS = ROOT / "models"


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def encode_texts(texts: list[str], *, use_embeddings: bool) -> np.ndarray:
    from app.nlp.normalize import normalize_text

    normalized = [normalize_text(t) for t in texts]

    if use_embeddings:
        try:
            from app.embeddings.encoder import encode_texts as embed

            vectors = embed(normalized)
            return np.array(vectors, dtype=np.float32)
        except Exception as exc:
            print(f"Embedding encoder unavailable ({exc}), falling back to TF-IDF", file=sys.stderr)

    from sklearn.feature_extraction.text import TfidfVectorizer

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    matrix = vectorizer.fit_transform(normalized)
    return matrix, vectorizer


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=Path, default=DATA / "intent_train.jsonl")
    parser.add_argument("--eval", type=Path, default=DATA / "intent_eval.jsonl")
    parser.add_argument("--output", type=Path, default=MODELS / "intent_v1.joblib")
    parser.add_argument("--min-macro-f1", type=float, default=0.75)
    parser.add_argument("--min-discussion-recall", type=float, default=0.6)
    parser.add_argument("--no-embeddings", action="store_true")
    args = parser.parse_args()

    train_rows = load_jsonl(args.train)
    eval_rows = load_jsonl(args.eval)
    if len(train_rows) < 20:
        print("Train dataset too small", file=sys.stderr)
        return 1

    train_texts = [r["text"] for r in train_rows]
    train_labels = [r["label"] for r in train_rows]
    eval_texts = [r["text"] for r in eval_rows]
    eval_labels = [r["label"] for r in eval_rows]

    use_embeddings = not args.no_embeddings
    vectorizer = None

    if use_embeddings:
        try:
            from app.embeddings.encoder import encode_texts as embed
            from app.nlp.normalize import normalize_text

            x_train = np.array(embed([normalize_text(t) for t in train_texts]), dtype=np.float32)
            x_eval = np.array(embed([normalize_text(t) for t in eval_texts]), dtype=np.float32)
            feature_type = "embeddings"
        except Exception:
            use_embeddings = False

    if not use_embeddings:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from app.nlp.normalize import normalize_text

        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        x_train = vectorizer.fit_transform([normalize_text(t) for t in train_texts])
        x_eval = vectorizer.transform([normalize_text(t) for t in eval_texts])
        feature_type = "tfidf"

    scaler = StandardScaler(with_mean=feature_type == "embeddings")
    if feature_type == "embeddings":
        x_train = scaler.fit_transform(x_train)
        x_eval = scaler.transform(x_eval)

    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    clf.fit(x_train, train_labels)
    pred = clf.predict(x_eval)

    macro_f1 = f1_score(eval_labels, pred, average="macro")
    report = classification_report(eval_labels, pred, output_dict=True)
    discussion_recall = report.get("discussion", {}).get("recall", 0.0)

    bundle = {
        "classifier": clf,
        "vectorizer": vectorizer,
        "scaler": scaler if feature_type == "embeddings" else None,
        "feature_type": feature_type,
        "labels": list(clf.classes_),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, args.output)

    meta = {
        "version": args.output.stem,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "train_size": len(train_rows),
        "eval_size": len(eval_rows),
        "feature_type": feature_type,
        "macro_f1": macro_f1,
        "discussion_recall": discussion_recall,
        "metrics": report,
    }
    meta_path = args.output.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(meta, ensure_ascii=False, indent=2))

    if macro_f1 < args.min_macro_f1:
        print(f"FAIL: macro-F1 {macro_f1:.3f} < {args.min_macro_f1}", file=sys.stderr)
        return 1
    if discussion_recall < args.min_discussion_recall:
        print(
            f"FAIL: discussion recall {discussion_recall:.3f} < {args.min_discussion_recall}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
