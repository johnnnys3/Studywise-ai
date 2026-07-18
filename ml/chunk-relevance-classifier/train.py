"""Fine-tunes DistilBERT as a binary (question, chunk) relevance classifier
on StudyWise's own RAG trace data (see prepare_data.py).

Usage (from repo root):
    /private/tmp/sw-venv/bin/python ml/chunk-relevance-classifier/train.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from datasets import Dataset
from sklearn.metrics import precision_recall_fscore_support, accuracy_score, confusion_matrix
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "model"
MODEL_NAME = "distilbert-base-uncased"
LABEL_NAMES = {0: "not_relevant", 1: "relevant"}


def load_split(name: str) -> Dataset:
    rows = [json.loads(line) for line in (DATA_DIR / f"{name}.jsonl").read_text().splitlines()]
    return Dataset.from_list(rows)


def main() -> None:
    train_ds = load_split("train")
    val_ds = load_split("validation")
    test_ds = load_split("test")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def tokenize(batch):
        return tokenizer(batch["question"], batch["chunk_text"], truncation=True, max_length=256)

    train_ds = train_ds.map(tokenize, batched=True)
    val_ds = val_ds.map(tokenize, batched=True)
    test_ds = test_ds.map(tokenize, batched=True)

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=2,
        id2label=LABEL_NAMES,
        label2id={v: k for k, v in LABEL_NAMES.items()},
    )

    collator = DataCollatorWithPadding(tokenizer=tokenizer)

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=-1)
        precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average="binary", zero_division=0)
        return {
            "accuracy": accuracy_score(labels, preds),
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

    args = TrainingArguments(
        output_dir=str(OUTPUT_DIR / "checkpoints"),
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=32,
        num_train_epochs=6,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_steps=10,
        report_to=[],
        save_total_limit=2,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=collator,
        processing_class=tokenizer,
        compute_metrics=compute_metrics,
    )

    trainer.train()

    val_metrics = trainer.evaluate(val_ds)
    test_metrics = trainer.evaluate(test_ds, metric_key_prefix="test")

    test_preds = trainer.predict(test_ds)
    test_pred_labels = np.argmax(test_preds.predictions, axis=-1)
    cm = confusion_matrix(test_preds.label_ids, test_pred_labels).tolist()

    final_dir = OUTPUT_DIR / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(final_dir))
    tokenizer.save_pretrained(str(final_dir))

    report = {
        "validation": val_metrics,
        "test": test_metrics,
        "test_confusion_matrix": {"labels": ["not_relevant", "relevant"], "matrix": cm},
        "train_size": len(train_ds),
        "validation_size": len(val_ds),
        "test_size": len(test_ds),
    }
    (OUTPUT_DIR / "metrics.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
