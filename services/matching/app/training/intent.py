"""Train intent classifier on frozen embeddings."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.preprocessing import StandardScaler

from app.config import INTENT_META_NAME, INTENT_MODEL_NAME
from app.paths import data_dir, models_dir


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def train_intent(
    *,
    train_path: Path | None = None,
    eval_path: Path | None = None,
    output_path: Path | None = None,
    min_macro_f1: float = 0.75,
    min_discussion_recall: float = 0.6,
    use_embeddings: bool = True,
) -> Path:
    data = data_dir()
    models = models_dir()
    train_file = train_path or data / "intent_train.jsonl"
    eval_file = eval_path or data / "intent_eval.jsonl"
    output = output_path or models / INTENT_MODEL_NAME

    train_rows = _load_jsonl(train_file)
    eval_rows = _load_jsonl(eval_file)
    if len(train_rows) < 20:
        raise RuntimeError("Train dataset too small")

    train_texts = [r["text"] for r in train_rows]
    train_labels = [r["label"] for r in train_rows]
    eval_texts = [r["text"] for r in eval_rows]
    eval_labels = [r["label"] for r in eval_rows]

    vectorizer = None
    feature_type = "tfidf"

    if use_embeddings:
        try:
            from app.embeddings.encoder import encode_texts as embed
            from app.nlp.normalize import normalize_text

            x_train = np.array(embed([normalize_text(t) for t in train_texts]), dtype=np.float32)
            x_eval = np.array(embed([normalize_text(t) for t in eval_texts]), dtype=np.float32)
            feature_type = "embeddings"
        except Exception as exc:
            print(f"Embedding encoder unavailable ({exc}), falling back to TF-IDF", file=sys.stderr)
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

    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, output)

    meta = {
        "version": INTENT_MODEL_NAME,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "train_size": len(train_rows),
        "eval_size": len(eval_rows),
        "feature_type": feature_type,
        "macro_f1": macro_f1,
        "discussion_recall": discussion_recall,
        "metrics": report,
    }
    meta_path = output.parent / INTENT_META_NAME
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(meta, ensure_ascii=False, indent=2))

    if macro_f1 < min_macro_f1:
        raise RuntimeError(f"macro-F1 {macro_f1:.3f} < {min_macro_f1}")
    if discussion_recall < min_discussion_recall:
        raise RuntimeError(f"discussion recall {discussion_recall:.3f} < {min_discussion_recall}")

    return output
