import math

from app.services import embeddings


def test_fallback_embed_text_returns_normalized_384_dim_vector() -> None:
    vector = embeddings._fallback_embed_text("Studying for the biology exam")

    assert len(vector) == embeddings.EMBEDDING_DIMENSIONS
    norm = math.sqrt(sum(value * value for value in vector))
    assert math.isclose(norm, 1.0, abs_tol=1e-6)


def test_embed_texts_batches_through_model_encode(monkeypatch) -> None:
    calls = []

    class FakeModel:
        def encode(self, texts, normalize_embeddings=True):
            calls.append(list(texts))
            return [[0.0] * embeddings.EMBEDDING_DIMENSIONS for _ in texts]

    monkeypatch.setattr(embeddings, "_get_model", lambda: FakeModel())

    texts = ["first chunk", "second chunk", "third chunk"]
    result = embeddings.embed_texts(texts)

    assert calls == [texts]
    assert len(result) == 3
    assert all(len(vector) == embeddings.EMBEDDING_DIMENSIONS for vector in result)


def test_embed_text_delegates_to_embed_texts(monkeypatch) -> None:
    seen = []

    def fake_embed_texts(texts, dimensions=embeddings.EMBEDDING_DIMENSIONS):
        seen.append(texts)
        return [[0.1] * dimensions]

    monkeypatch.setattr(embeddings, "embed_texts", fake_embed_texts)

    result = embeddings.embed_text("solo text")

    assert seen == [["solo text"]]
    assert result == [0.1] * embeddings.EMBEDDING_DIMENSIONS


def test_embed_texts_falls_back_when_model_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(embeddings, "_get_model", lambda: None)

    result = embeddings.embed_texts(["fallback path text"])

    assert len(result) == 1
    assert len(result[0]) == embeddings.EMBEDDING_DIMENSIONS
    norm = math.sqrt(sum(value * value for value in result[0]))
    assert math.isclose(norm, 1.0, abs_tol=1e-6)
