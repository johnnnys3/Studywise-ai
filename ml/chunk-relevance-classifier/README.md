---
license: apache-2.0
base_model: distilbert-base-uncased
tags:
  - text-classification
  - retrieval
  - rag
  - distilbert
datasets: []
metrics:
  - accuracy
  - precision
  - recall
  - f1
pipeline_tag: text-classification
---

# StudyWise Chunk Relevance Classifier

A DistilBERT model fine-tuned to judge whether a retrieved text chunk is actually relevant to a user's question, for the [StudyWise](https://github.com/johnnnys3/Studywise-ai) RAG pipeline.

Given a `(question, chunk_text)` pair, the model predicts one of two labels:

- `relevant` — the chunk should be used to answer the question
- `not_relevant` — the chunk is off-topic or was a weak retrieval candidate

## Intended use

Meant as a lightweight re-ranking / filtering signal sitting after StudyWise's hybrid retriever (keyword + proposition + embedding search) and before answer generation — catching cases where the hybrid retriever's score doesn't reflect true relevance.

This is a small-scale training exercise tied to a specific student project, not a production-grade reranker. See **Limitations** before relying on it.

## Training data

Built from StudyWise's own `rag_traces` — real (question, retrieved-chunk, hybrid-retrieval-score) records logged by the app's retriever — plus explicit cross-document negatives, via [`prepare_data.py`](./prepare_data.py):

- **Positive** (`relevant`, label `1`): chunk ranked in the top 2 hybrid-retrieval results for a question.
- **Hard negative** (`not_relevant`, label `0`): chunk was retrieved as a candidate for the question but ranked below the top 2.
- **Easy negative** (`not_relevant`, label `0`): chunk sampled from a document unrelated to the question's source document — guaranteed irrelevant.

Split **by question** (not by row) to prevent the same question's phrasing from leaking across train/validation/test.

| Split | Examples | Unique questions | % relevant |
|---|---|---|---|
| train | 481 | 8 | 23.1% |
| validation | 172 | 2 | 22.1% |
| test | 99 | 2 | 26.3% |

## Training procedure

- Base model: `distilbert-base-uncased`
- Input: `question` and `chunk_text` encoded as a sentence pair (`[CLS] question [SEP] chunk_text [SEP]`), max length 256
- 6 epochs, learning rate 2e-5, batch size 16, weight decay 0.01
- Best checkpoint selected by validation F1
- Full script: [`train.py`](./train.py)

## Results (held-out test split)

| Metric | Value |
|---|---|
| Accuracy | 0.717 |
| Precision | 0.458 |
| Recall | 0.423 |
| F1 | 0.440 |

Confusion matrix (test, n=99):

| | Predicted not_relevant | Predicted relevant |
|---|---|---|
| **Actual not_relevant** | 60 | 13 |
| **Actual relevant** | 15 | 11 |

## Limitations

- **Small, low-diversity source data.** The underlying trace log covers only 12 unique questions (all biology/ecology content from test/eval documents), split 8/2/2. The reported metrics are indicative of the approach, not a reliable estimate of real-world performance — treat them as a training exercise, not a benchmark.
- **Below-baseline raw accuracy.** A trivial "always predict not_relevant" baseline scores 0.737 accuracy on this test split (since ~74% of pairs are negative), higher than this model's 0.717. The model trades some accuracy for actually catching relevant chunks (F1 0.44 vs. the baseline's 0.0 F1 on the positive class), which is the more useful trade-off for a retrieval filter, but it means accuracy alone is a misleading headline metric here.
- **Domain-narrow.** Trained entirely on biology/ecology chunks; unlikely to generalize to other subjects without more data.

## Usage

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

tokenizer = AutoTokenizer.from_pretrained("REPO_ID")
model = AutoModelForSequenceClassification.from_pretrained("REPO_ID")

question = "What happens during the electron transport chain?"
chunk = "The electron transport chain is located in the inner mitochondrial membrane."

inputs = tokenizer(question, chunk, return_tensors="pt", truncation=True, max_length=256)
with torch.no_grad():
    logits = model(**inputs).logits
prediction = model.config.id2label[logits.argmax().item()]
print(prediction)
```
