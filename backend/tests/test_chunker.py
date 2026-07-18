from app.services.chunker import chunk_text, semantic_chunk_pages


def test_chunk_text_creates_overlapping_chunks() -> None:
    text = " ".join(f"word{i}" for i in range(1000))
    chunks = chunk_text(text, chunk_size=200, overlap=50)

    assert len(chunks) > 1
    assert chunks[0].token_count == 200
    assert chunks[1].chunk_text.startswith("word150")


def test_lowercase_standalone_line_is_detected_as_heading() -> None:
    text = (
        "results and discussion\n\n"
        "The experiment showed a significant increase in reaction rate when temperature was raised.\n\n"
        "conclusion\n\n"
        "Overall the findings support the initial hypothesis."
    )
    chunks = semantic_chunk_pages([{"page_number": 1, "text": text}])

    assert chunks[0].section_title == "results and discussion"
    assert chunks[0].chunk_text.startswith("The experiment showed")
    assert chunks[1].section_title == "conclusion"
