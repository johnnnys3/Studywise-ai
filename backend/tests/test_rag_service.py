from app.services.rag_service import _compress_relevant_sentences, _split_sentences


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


def test_compress_relevant_sentences_prefers_topical_chunk_over_keyword_coincidence() -> None:
    # "the powerhouse of the cell because of this role" shares two raw
    # keywords with the question ("cell", "role"), but it's not actually
    # about ribosomes. Raw keyword-overlap counting ranks it above the
    # genuinely relevant sentence, which only shares one keyword
    # ("ribosomes"). The chunk's own retrieval relevance (cross-encoder
    # score here) should break that tie correctly.
    query_terms = {"role", "ribosomes", "cell"}
    chunks = [
        {
            "chunk_text": (
                "Mitochondria are organelles that generate most of a cell's chemical energy "
                "through cellular respiration, producing ATP from glucose and oxygen. "
                "They are often called the powerhouse of the cell because of this role."
            ),
            "cross_encoder_score": -1.465,
        },
        {
            "chunk_text": (
                "The nucleus stores a cell's genetic information as DNA, organized into chromosomes. "
                "Ribosomes read messenger RNA copied from DNA and assemble amino acids into proteins, "
                "a process called translation."
            ),
            "cross_encoder_score": 4.142,
        },
    ]

    selected = _compress_relevant_sentences(query_terms, chunks)

    assert selected[0].startswith("Ribosomes read messenger RNA")


def test_split_sentences_does_not_break_on_pdf_line_wraps() -> None:
    # PDF text extraction wraps lines with single "\n" mid-sentence; only
    # "\n\n" (or more) marks an actual paragraph break, and even that
    # shouldn't fragment a sentence that has no terminal punctuation yet.
    text = "Ribosomes read messenger RNA copied from DNA and assemble\namino acids into proteins, a process called translation."

    assert _split_sentences(text) == [
        "Ribosomes read messenger RNA copied from DNA and assemble amino acids into proteins, a process called translation."
    ]


def test_split_sentences_still_splits_on_sentence_boundaries() -> None:
    text = "First sentence here. Second sentence follows!\nThird one wraps\nacross lines?"

    assert _split_sentences(text) == [
        "First sentence here.",
        "Second sentence follows!",
        "Third one wraps across lines?",
    ]
