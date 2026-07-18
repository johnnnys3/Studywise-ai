from app.services.rag_service import _compress_relevant_sentences


def test_compress_relevant_sentences_ranks_globally_not_per_chunk() -> None:
    # A relevant sentence in the second chunk must outrank irrelevant
    # sentences in the first chunk, instead of every sentence of chunk 1
    # being exhausted before chunk 2 is even considered.
    query_terms = {"ribosomes", "proteins"}
    chunks = [
        {"chunk_text": "The cat sat on the mat. The dog ran in the park. A bird flew over the house."},
        {"chunk_text": "Ribosomes make proteins."},
    ]

    selected = _compress_relevant_sentences(query_terms, chunks)

    assert selected[0] == "Ribosomes make proteins."
