from app.services.quiz_generator import _generate_local_questions


def test_local_quiz_questions_use_document_content() -> None:
    chunks = [
        {
            "chunk_text": "Retrieval augmented generation improves study answers by retrieving relevant source chunks before generation. Citations help students verify claims from uploaded material.",
            "page_number": 1,
        },
        {
            "chunk_text": "Weak topic tracking uses quiz mistakes to recommend which concepts a student should review next. Progress data is updated after every quiz attempt.",
            "page_number": 2,
        },
    ]

    questions = _generate_local_questions(chunks, 2)

    assert len(questions) == 2
    assert "is discussed in the uploaded material" not in questions[0]["correct_answer"]
    assert any("retrieving relevant source chunks" in option for option in questions[0]["options_json"])
