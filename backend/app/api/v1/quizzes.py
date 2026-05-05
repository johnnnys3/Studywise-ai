from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.services.quiz_generator import generate_quiz, submit_attempt
from app.storage import store


router = APIRouter()


class QuizCreateRequest(BaseModel):
    question_count: int = Field(default=5, ge=1, le=20)
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")


class QuizAttemptRequest(BaseModel):
    answers: dict[str, str]


def quiz_with_questions(quiz: dict) -> dict:
    return {**quiz, "questions": store.filter("quiz_questions", quiz_id=quiz["id"])}


@router.post("/documents/{document_id}/quizzes")
def create_quiz(document_id: str, payload: QuizCreateRequest, current_user: dict = Depends(get_current_user)) -> dict:
    document = store.find("documents", id=document_id, user_id=current_user["id"])
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    try:
        return generate_quiz(current_user["id"], document_id, payload.question_count, payload.difficulty)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/quizzes")
def list_quizzes(current_user: dict = Depends(get_current_user)) -> list[dict]:
    quizzes = store.filter("quizzes", user_id=current_user["id"])
    return [quiz_with_questions(quiz) for quiz in sorted(quizzes, key=lambda item: item["created_at"], reverse=True)]


@router.get("/quizzes/{quiz_id}")
def get_quiz(quiz_id: str, current_user: dict = Depends(get_current_user)) -> dict:
    quiz = store.find("quizzes", id=quiz_id, user_id=current_user["id"])
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")
    return quiz_with_questions(quiz)


@router.post("/quizzes/{quiz_id}/attempts")
def create_attempt(quiz_id: str, payload: QuizAttemptRequest, current_user: dict = Depends(get_current_user)) -> dict:
    try:
        return submit_attempt(current_user["id"], quiz_id, payload.answers)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/quizzes/{quiz_id}/attempts")
def list_attempts(quiz_id: str, current_user: dict = Depends(get_current_user)) -> list[dict]:
    quiz = store.find("quizzes", id=quiz_id, user_id=current_user["id"])
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found.")
    return store.filter("quiz_attempts", user_id=current_user["id"], quiz_id=quiz_id)
