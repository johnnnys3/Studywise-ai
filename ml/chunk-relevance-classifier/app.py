"""Gradio demo for the StudyWise chunk relevance classifier.

Run locally:
    /private/tmp/sw-venv/bin/python ml/chunk-relevance-classifier/app.py

When deployed as a HF Space, set MODEL_ID to the pushed Hub repo id.
"""

from __future__ import annotations

import os
from pathlib import Path

import gradio as gr
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

DEFAULT_MODEL_PATH = str(Path(__file__).resolve().parent / "model" / "final")
MODEL_ID = os.environ.get("MODEL_ID", DEFAULT_MODEL_PATH)

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID)
model.eval()

EXAMPLES = [
    [
        "What happens during the electron transport chain?",
        "The electron transport chain is located in the inner mitochondrial membrane.",
    ],
    [
        "Where does photosynthesis take place in a plant cell?",
        "Cellular respiration is the process by which cells convert glucose and oxygen into usable energy.",
    ],
]


def classify(question: str, chunk_text: str) -> dict[str, float]:
    if not question.strip() or not chunk_text.strip():
        return {}
    inputs = tokenizer(question, chunk_text, return_tensors="pt", truncation=True, max_length=256)
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=-1)[0]
    return {model.config.id2label[i]: float(probs[i]) for i in range(len(probs))}


demo = gr.Interface(
    fn=classify,
    inputs=[
        gr.Textbox(label="Question", placeholder="What happens during the electron transport chain?"),
        gr.Textbox(label="Candidate chunk", lines=4, placeholder="Paste a retrieved chunk of text here..."),
    ],
    outputs=gr.Label(label="Relevance"),
    examples=EXAMPLES,
    title="StudyWise Chunk Relevance Classifier",
    description=(
        "DistilBERT fine-tuned on StudyWise's own RAG retrieval traces to judge whether a retrieved "
        "chunk actually answers a question. See the model card for training data and metrics."
    ),
)

if __name__ == "__main__":
    demo.launch()
