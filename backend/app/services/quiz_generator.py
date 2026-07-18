import logging
import re
from typing import Any

from app.prompts.rag_prompts import QUIZ_GENERATION_SYSTEM_PROMPT
from app.services.llm_service import create_structured_response, is_ai_configured
from app.storage import store

_logger = logging.getLogger(__name__)


_TOPIC_STOPWORDS = {
    "which", "there", "their", "about", "should", "would", "could", "because", "material",
    "during", "these", "those", "other", "another", "several", "various", "within", "using",
    "called", "primarily", "essential", "critical", "directly", "indirectly", "similarly",
    "conversely", "additionally", "therefore", "however", "although", "typically", "usually",
    "including", "specifically", "immediately", "beyond", "through", "before", "after",
    "between", "against", "while", "where", "when", "then", "than", "also", "such", "some",
    "does", "each", "every", "being", "become", "becomes", "first", "second", "third", "result",
    "resulting", "process", "processes",
}


def _topic_from_text(text: str) -> str:
    candidates = [
        word.strip("-").title()
        for word in re.findall(r"[A-Za-z][a-zA-Z-]{4,}", text)
        if word.lower() not in _TOPIC_STOPWORDS
    ]
    if not candidates:
        return "Core Concepts"
    long_candidates = [word for word in candidates if len(word) >= 7]
    return (long_candidates or candidates)[0]


def generate_quiz(user_id: str, document_id: str, question_count: int, difficulty: str) -> dict[str, Any]:
    chunks = store.filter("document_chunks", user_id=user_id, document_id=document_id)
    if not chunks:
        raise ValueError("Document has no processed chunks.")

    document = store.find("documents", id=document_id, user_id=user_id)
    quiz = store.insert(
        "quizzes",
        {
            "user_id": user_id,
            "document_id": document_id,
            "title": f"{document['title']} study quiz" if document else "Study quiz",
            "difficulty": difficulty,
            "question_count": question_count,
        },
    )

    evidence_chunks = _select_quiz_evidence(chunks, question_count, difficulty)

    valid_payloads: list[dict[str, Any]] = []
    if is_ai_configured():
        valid_payloads = _generate_ai_questions_until_count(evidence_chunks, question_count, difficulty)

    if len(valid_payloads) < question_count:
        seen_questions = {str(p["question"]).lower() for p in valid_payloads}
        local_candidates = _validate_question_payloads(
            _generate_local_questions(evidence_chunks, question_count * 2, difficulty),
            evidence_chunks,
            difficulty,
        )
        for payload in local_candidates:
            if len(valid_payloads) >= question_count:
                break
            question_key = str(payload["question"]).lower()
            if question_key in seen_questions:
                continue
            seen_questions.add(question_key)
            valid_payloads.append(payload)

    questions: list[dict[str, Any]] = []
    if not valid_payloads:
        raise ValueError("Quiz generation failed validation. Please try again.")

    for payload in valid_payloads[:question_count]:
        question = store.insert("quiz_questions", {"quiz_id": quiz["id"], **payload})
        questions.append(question)

    return {**quiz, "questions": questions}


def _generate_local_questions(chunks: list[dict[str, Any]], question_count: int, difficulty: str = "medium") -> list[dict[str, Any]]:
    questions = []
    candidate_items = _candidate_items_from_chunks(chunks)
    if not candidate_items:
        return []

    for index, item in enumerate(candidate_items[:question_count]):
        topic = item.get("topic") or _topic_from_text(item["sentence"])
        distractors = _build_distractors(item["answer"], candidate_items, index)
        options = [item["answer"], *distractors]
        cognitive_skill = _local_cognitive_skill(difficulty, index)
        question_text = _local_question_text(item, topic, difficulty, cognitive_skill)
        questions.append(
            {
                "question": question_text,
                "options_json": _rotate_options(options, index),
                "correct_answer": item["answer"],
                "explanation": f"Page {item['source_page']} supports this answer: {item['sentence']}",
                "difficulty": difficulty,
                "topic": topic,
                "source_page": item["source_page"],
                "source_chunk_id": item.get("source_chunk_id", ""),
                "cognitive_skill": cognitive_skill,
            }
        )
    return questions


def _candidate_items_from_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen_answers: set[str] = set()
    for chunk in chunks:
        propositions = store.filter("chunk_propositions", chunk_id=chunk.get("id", ""))
        for proposition in sorted(propositions, key=lambda item: -float(item.get("quality_score", 0))):
            statement = str(proposition.get("statement", "")).strip()
            answer = _shorten_option(statement)
            if not answer or answer.lower() in seen_answers:
                continue
            seen_answers.add(answer.lower())
            items.append(
                {
                    "sentence": statement,
                    "answer": answer,
                    "source_page": proposition.get("page_number", chunk["page_number"]),
                    "source_chunk_id": chunk.get("id", ""),
                    "topic": proposition.get("topic"),
                    "content_type": proposition.get("content_type"),
                }
            )
        for sentence in _extract_meaningful_sentences(chunk["chunk_text"]):
            answer = _shorten_option(sentence)
            if answer.lower() in seen_answers:
                continue
            seen_answers.add(answer.lower())
            items.append(
                {
                    "sentence": sentence,
                    "answer": answer,
                    "source_page": chunk["page_number"],
                    "source_chunk_id": chunk.get("id", ""),
                    "topic": chunk.get("section_title"),
                }
            )
    return items


def _extract_meaningful_sentences(text: str) -> list[str]:
    raw_sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    sentences = []
    for sentence in raw_sentences:
        normalized = re.sub(r"\s+", " ", sentence).strip(" -")
        word_count = len(normalized.split())
        if 8 <= word_count <= 35 and any(char.isalpha() for char in normalized):
            sentences.append(normalized)
    if sentences:
        return sentences

    words = text.split()
    if len(words) >= 8:
        return [" ".join(words[: min(len(words), 28)]).strip()]
    return []


def _shorten_option(sentence: str) -> str:
    sentence = sentence.strip()
    if len(sentence) <= 180:
        return sentence
    words = sentence.split()
    shortened: list[str] = []
    for word in words:
        if len(" ".join(shortened + [word])) > 177:
            break
        shortened.append(word)
    return f"{' '.join(shortened).rstrip('.,;:')}..."


def _build_distractors(correct_answer: str, candidates: list[dict[str, Any]], current_index: int) -> list[str]:
    other_indexes = [index for index in range(len(candidates)) if index != current_index]
    rotated_indexes = other_indexes[current_index % max(len(other_indexes), 1):] + other_indexes[: current_index % max(len(other_indexes), 1)]
    distractors = []
    for index in rotated_indexes:
        answer = candidates[index]["answer"]
        if answer == correct_answer or answer in distractors:
            continue
        distractors.append(answer)
        if len(distractors) == 3:
            break

    generic_distractors = [
        "The material says this topic is not covered in the selected document.",
        "The material says citations are not needed to support study answers.",
        "The material says quiz results should not affect topic recommendations.",
    ]
    for distractor in generic_distractors:
        if len(distractors) == 3:
            break
        if distractor != correct_answer:
            distractors.append(distractor)
    return distractors[:3]


def _rotate_options(options: list[str], offset: int) -> list[str]:
    clean_options = []
    for option in options:
        if option not in clean_options:
            clean_options.append(option)
    while len(clean_options) < 4:
        clean_options.append("The uploaded material does not provide enough evidence for this statement.")
    offset = offset % 4
    return clean_options[offset:] + clean_options[:offset]


_MAX_QUESTIONS_PER_AI_CALL = 4


def _generate_ai_questions_until_count(
    chunks: list[dict[str, Any]], question_count: int, difficulty: str, max_attempts: int | None = None
) -> list[dict[str, Any]]:
    batches_needed = (question_count + _MAX_QUESTIONS_PER_AI_CALL - 1) // _MAX_QUESTIONS_PER_AI_CALL
    if max_attempts is None:
        max_attempts = max(3, batches_needed + 1)
    collected: list[dict[str, Any]] = []
    seen_questions: set[str] = set()
    for _ in range(max_attempts):
        remaining = question_count - len(collected)
        if remaining <= 0:
            break
        batch_count = min(remaining, _MAX_QUESTIONS_PER_AI_CALL)
        raw_payloads = _generate_ai_questions(chunks, batch_count, difficulty, exclude_questions=seen_questions)
        if not raw_payloads:
            _logger.warning(
                "AI quiz generation returned no usable questions for this batch (requested %d, have %d/%d so far).",
                batch_count,
                len(collected),
                question_count,
            )
            continue
        valid_batch = _validate_question_payloads(raw_payloads, chunks, difficulty)
        if len(valid_batch) < len(raw_payloads):
            _logger.warning(
                "AI returned %d question(s) but only %d passed validation (duplicate/generic/malformed filtering).",
                len(raw_payloads),
                len(valid_batch),
            )
        for payload in valid_batch:
            if len(collected) >= question_count:
                break
            question_key = str(payload["question"]).lower()
            if question_key in seen_questions:
                continue
            seen_questions.add(question_key)
            collected.append(payload)
    if len(collected) < question_count:
        _logger.warning(
            "AI quiz generation produced only %d/%d requested questions after %d attempts; backfilling with local generator.",
            len(collected),
            question_count,
            max_attempts,
        )
    return collected


def _generate_ai_questions(
    chunks: list[dict[str, Any]],
    question_count: int,
    difficulty: str,
    exclude_questions: set[str] | None = None,
) -> list[dict[str, Any]]:
    selected_chunks = chunks[: min(max(question_count * 2, 4), 12)]
    context = "\n\n".join(
        (
            f"[source_page: {chunk['page_number']} | source_chunk_id: {chunk.get('id', '')} | "
            f"chunk_number: {chunk['chunk_index'] + 1} | section: {chunk.get('section_title') or 'Untitled'} | "
            f"content_type: {chunk.get('content_type', 'paragraph')}]\n{chunk['chunk_text']}"
        )
        for chunk in selected_chunks
    )
    system_instructions = (
        f"{QUIZ_GENERATION_SYSTEM_PROMPT} Each question must have exactly four unique plausible options, "
        "one correct answer copied exactly from options, an educational explanation, difficulty, topic, "
        "source_page, source_chunk_id, and cognitive_skill. Do not invent source pages or chunk IDs. "
        f"You must return exactly {question_count} questions in the array, no more and no fewer."
    )
    exclusion_text = (
        f"Do not repeat or closely rephrase these already-used questions:\n{chr(10).join(sorted(exclude_questions))}\n\n"
        if exclude_questions
        else ""
    )
    user_input = (
        f"Difficulty: {difficulty}\n"
        f"Number of questions: {question_count}\n\n"
        f"Difficulty rules:\n{_difficulty_rules(difficulty)}\n\n"
        f"{exclusion_text}"
        f"Allowed source_chunk_id values:\n{', '.join(str(chunk.get('id', '')) for chunk in selected_chunks)}\n\n"
        f"Study context:\n{context}"
    )
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["questions"],
        "properties": {
            "questions": {
                "type": "array",
                "minItems": question_count,
                "maxItems": question_count,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "question",
                        "options",
                        "correct_answer",
                        "explanation",
                        "difficulty",
                        "topic",
                        "source_page",
                        "source_chunk_id",
                        "cognitive_skill",
                    ],
                    "properties": {
                        "question": {"type": "string"},
                        "options": {
                            "type": "array",
                            "minItems": 4,
                            "maxItems": 4,
                            "items": {"type": "string"},
                        },
                        "correct_answer": {"type": "string"},
                        "explanation": {"type": "string"},
                        "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
                        "topic": {"type": "string"},
                        "source_page": {"type": "integer"},
                        "source_chunk_id": {"type": "string"},
                        "cognitive_skill": {
                            "type": "string",
                            "enum": [
                                "recall",
                                "definition",
                                "comparison",
                                "cause_effect",
                                "process_order",
                                "application",
                                "inference",
                                "misconception_check",
                            ],
                        },
                    },
                },
            }
        },
    }
    response = _create_quiz_json_with_retry(system_instructions, user_input, schema)
    if not response:
        return []

    questions = []
    valid_pages = {int(chunk["page_number"]) for chunk in selected_chunks}
    valid_chunk_ids = {str(chunk.get("id", "")) for chunk in selected_chunks}
    for item in response.get("questions", []):
        options = [str(option).strip() for option in item.get("options", []) if str(option).strip()]
        answer = str(item.get("correct_answer", "")).strip()
        source_page = int(item.get("source_page", selected_chunks[0]["page_number"]))
        source_chunk_id = str(item.get("source_chunk_id", "")).strip()
        if len(options) != 4 or answer not in options or source_chunk_id not in valid_chunk_ids:
            continue
        if source_page not in valid_pages:
            continue
        questions.append(
            {
                "question": str(item["question"]).strip(),
                "options_json": options,
                "correct_answer": answer,
                "explanation": str(item["explanation"]).strip(),
                "difficulty": str(item["difficulty"]).strip(),
                "topic": str(item["topic"]).strip() or "Core Concepts",
                "source_page": source_page,
                "source_chunk_id": source_chunk_id,
                "cognitive_skill": str(item["cognitive_skill"]).strip(),
            }
        )
    return questions


def submit_attempt(user_id: str, quiz_id: str, answers: dict[str, str]) -> dict[str, Any]:
    quiz = store.find("quizzes", id=quiz_id, user_id=user_id)
    if not quiz:
        raise ValueError("Quiz not found.")

    questions = store.filter("quiz_questions", quiz_id=quiz_id)
    correct_count = 0
    answer_rows = []
    for question in questions:
        selected_answer = answers.get(question["id"], "")
        is_correct = selected_answer == question["correct_answer"]
        if is_correct:
            correct_count += 1
        answer_rows.append(
            store.insert(
                "quiz_answers",
                {
                    "attempt_id": "",
                    "question_id": question["id"],
                    "selected_answer": selected_answer,
                    "is_correct": is_correct,
                    "topic": question["topic"],
                },
            )
        )
        _update_weak_topic(
            user_id,
            question["topic"],
            is_correct,
            document_id=quiz["document_id"],
            source_page=question.get("source_page"),
            source_chunk_id=question.get("source_chunk_id"),
            difficulty=question.get("difficulty", quiz.get("difficulty")),
            cognitive_skill=question.get("cognitive_skill"),
        )

    total = max(len(questions), 1)
    attempt = store.insert(
        "quiz_attempts",
        {
            "user_id": user_id,
            "quiz_id": quiz_id,
            "score": correct_count,
            "total_questions": len(questions),
            "percentage": round((correct_count / total) * 100, 1),
        },
    )
    for answer in answer_rows:
        store.update("quiz_answers", answer["id"], {"attempt_id": attempt["id"]})

    return {**attempt, "answers": store.filter("quiz_answers", attempt_id=attempt["id"])}


def _update_weak_topic(
    user_id: str,
    topic: str,
    is_correct: bool,
    document_id: str | None = None,
    source_page: int | None = None,
    source_chunk_id: str | None = None,
    difficulty: str | None = None,
    cognitive_skill: str | None = None,
) -> None:
    current = store.find("weak_topics", user_id=user_id, topic=topic)
    review_recommendation = _review_recommendation(topic, source_page, source_chunk_id)
    if current:
        correct_count = int(current.get("correct_count", 0)) + (1 if is_correct else 0)
        incorrect_count = int(current.get("incorrect_count", 0)) + (0 if is_correct else 1)
        total = max(correct_count + incorrect_count, 1)
        store.update(
            "weak_topics",
            current["id"],
            {
                "correct_count": correct_count,
                "incorrect_count": incorrect_count,
                "accuracy": round((correct_count / total) * 100, 1),
                "document_id": document_id or current.get("document_id"),
                "source_page": source_page or current.get("source_page"),
                "source_chunk_id": source_chunk_id or current.get("source_chunk_id"),
                "difficulty": difficulty or current.get("difficulty"),
                "cognitive_skill": cognitive_skill or current.get("cognitive_skill"),
                "review_recommendation": review_recommendation,
            },
        )
        return

    store.insert(
        "weak_topics",
        {
            "user_id": user_id,
            "topic": topic,
            "document_id": document_id,
            "source_page": source_page,
            "source_chunk_id": source_chunk_id,
            "difficulty": difficulty,
            "cognitive_skill": cognitive_skill,
            "correct_count": 1 if is_correct else 0,
            "incorrect_count": 0 if is_correct else 1,
            "accuracy": 100.0 if is_correct else 0.0,
            "review_recommendation": review_recommendation,
            "last_reviewed_at": None,
        },
    )


def _select_quiz_evidence(chunks: list[dict[str, Any]], question_count: int, difficulty: str) -> list[dict[str, Any]]:
    min_tokens = {"easy": 20, "medium": 35, "hard": 45}.get(difficulty, 35)
    candidates = [
        chunk
        for chunk in chunks
        if int(chunk.get("token_count", 0)) >= min_tokens and float(chunk.get("quality_score", 0.5)) >= 0.25
    ] or chunks
    sorted_candidates = sorted(
        candidates,
        key=lambda chunk: (
            str(chunk.get("section_title") or ""),
            -float(chunk.get("quality_score", 0.0)),
            int(chunk.get("chunk_index", 0)),
        ),
    )
    selected: list[dict[str, Any]] = []
    used_sections: set[str] = set()
    for chunk in sorted_candidates:
        section = str(chunk.get("section_title") or chunk.get("page_number"))
        if section in used_sections and len(selected) < question_count:
            continue
        selected.append(chunk)
        used_sections.add(section)
        if len(selected) >= max(question_count * 2, 8):
            break
    if len(selected) < max(question_count, 4):
        for chunk in candidates:
            if chunk not in selected:
                selected.append(chunk)
            if len(selected) >= max(question_count * 2, 8):
                break
    return selected


def _validate_question_payloads(
    payloads: list[dict[str, Any]],
    evidence_chunks: list[dict[str, Any]],
    requested_difficulty: str,
) -> list[dict[str, Any]]:
    valid_chunk_ids = {str(chunk.get("id", "")) for chunk in evidence_chunks}
    valid_pages = {int(chunk.get("page_number", 1)) for chunk in evidence_chunks}
    valid: list[dict[str, Any]] = []
    seen_questions: set[str] = set()
    for payload in payloads:
        question = str(payload.get("question", "")).strip()
        options = [str(option).strip() for option in payload.get("options_json", []) if str(option).strip()]
        correct_answer = str(payload.get("correct_answer", "")).strip()
        source_chunk_id = str(payload.get("source_chunk_id", "")).strip()
        source_page = int(payload.get("source_page", 0) or 0)
        if _is_generic_question(question):
            continue
        if question.lower() in seen_questions:
            continue
        if len(options) != 4 or len(set(option.lower() for option in options)) != 4:
            continue
        if correct_answer not in options:
            continue
        if source_chunk_id and source_chunk_id not in valid_chunk_ids:
            continue
        if source_page not in valid_pages:
            continue
        detected = _detect_question_difficulty(payload)
        if requested_difficulty == "hard" and detected == "easy":
            continue
        payload["difficulty"] = requested_difficulty
        payload.setdefault("cognitive_skill", _local_cognitive_skill(requested_difficulty, len(valid)))
        seen_questions.add(question.lower())
        valid.append(payload)
    return valid


def _create_quiz_json_with_retry(system_instructions: str, user_input: str, schema: dict[str, Any]) -> dict[str, Any] | None:
    for attempt in range(2):
        try:
            return create_structured_response(system_instructions, user_input, "studywise_quiz", schema)
        except Exception:
            _logger.warning(
                "AI quiz generation call failed (attempt %d/2); falling back to local generator if this exhausts retries.",
                attempt + 1,
                exc_info=True,
            )
            if attempt == 1:
                return None
    return None


def _difficulty_rules(difficulty: str) -> str:
    rules = {
        "easy": (
            "Test definitions, basic facts, simple recall, and direct understanding. "
            "The answer should be clearly supported by one chunk. Use simple wording and avoid trick questions."
        ),
        "medium": (
            "Test relationships, comparisons, causes, processes, and application. "
            "Questions may connect two related ideas from the chunks. Explanations should teach why the answer is correct."
        ),
        "hard": (
            "Test inference, analysis, scenario-based reasoning, edge cases, trade-offs, and deeper understanding. "
            "Require combining multiple document-backed ideas without going outside the provided chunks. Distractors must be plausible."
        ),
    }
    return rules.get(difficulty, rules["medium"])


def _local_cognitive_skill(difficulty: str, index: int) -> str:
    skills = {
        "easy": ["definition", "recall"],
        "medium": ["comparison", "cause_effect", "process_order", "application"],
        "hard": ["inference", "application", "misconception_check"],
    }
    options = skills.get(difficulty, skills["medium"])
    return options[index % len(options)]


def _local_question_text(item: dict[str, Any], topic: str, difficulty: str, cognitive_skill: str) -> str:
    if difficulty == "easy":
        return f"Which option best states the document's direct point about {topic}?"
    if difficulty == "hard":
        return f"A student is trying to reason about {topic}. Which option is best supported by the source material?"
    if cognitive_skill == "comparison":
        return f"Which option best captures the relationship involving {topic} described in the document?"
    return f"Which option best applies the document's explanation of {topic}?"


def _is_generic_question(question: str) -> bool:
    lowered = question.lower()
    banned = [
        "main topic of the document",
        "which of the following is mentioned",
        "what is this document about",
        "according to the document, which",
        "which statement is true",
    ]
    return any(pattern in lowered for pattern in banned) or len(question.split()) < 6


def _detect_question_difficulty(payload: dict[str, Any]) -> str:
    question = str(payload.get("question", "")).lower()
    skill = str(payload.get("cognitive_skill", "")).lower()
    if skill in {"inference", "misconception_check"} or any(term in question for term in ["scenario", "student", "trade-off", "reason"]):
        return "hard"
    if skill in {"comparison", "cause_effect", "process_order", "application"} or any(term in question for term in ["why", "relationship", "process", "apply"]):
        return "medium"
    return "easy"


def _review_recommendation(topic: str, source_page: int | None, source_chunk_id: str | None) -> str:
    if source_page and source_chunk_id:
        return f"Review {topic} on page {source_page}, then retry questions from source chunk {source_chunk_id}."
    if source_page:
        return f"Review {topic} on page {source_page}, then retry a short focused quiz."
    return f"Review the source material related to {topic}, then retry a short focused quiz."
