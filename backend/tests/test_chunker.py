from app.services.chunker import chunk_text


def test_chunk_text_creates_overlapping_chunks() -> None:
    text = " ".join(f"word{i}" for i in range(1000))
    chunks = chunk_text(text, chunk_size=200, overlap=50)

    assert len(chunks) > 1
    assert chunks[0].token_count == 200
    assert chunks[1].chunk_text.startswith("word150")
