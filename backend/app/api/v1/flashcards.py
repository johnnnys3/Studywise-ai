from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.services.flashcard_generator import generate_flashcards
from app.storage import store


router = APIRouter()


@router.post("/{document_id}/flashcards")
def create_flashcards(document_id: str, current_user: dict = Depends(get_current_user)) -> list[dict]:
    document = store.find("documents", id=document_id, user_id=current_user["id"])
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    return generate_flashcards(current_user["id"], document_id)


@router.get("/{document_id}/flashcards")
def list_flashcards(document_id: str, current_user: dict = Depends(get_current_user)) -> list[dict]:
    document = store.find("documents", id=document_id, user_id=current_user["id"])
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    return store.filter("flashcards", user_id=current_user["id"], document_id=document_id)
