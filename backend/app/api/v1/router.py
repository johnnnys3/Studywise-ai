from fastapi import APIRouter

from app.api.v1 import auth, documents, evaluation, flashcards, progress, quizzes, rag, users


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(rag.router, prefix="/documents", tags=["rag"])
api_router.include_router(quizzes.router, tags=["quizzes"])
api_router.include_router(flashcards.router, prefix="/documents", tags=["flashcards"])
api_router.include_router(progress.router, prefix="/progress", tags=["progress"])
api_router.include_router(evaluation.router, prefix="/evaluation", tags=["evaluation"])
