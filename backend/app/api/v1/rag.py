from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.services.rag_service import build_answer
from app.storage import store


router = APIRouter()


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


@router.post("/{document_id}/ask")
def ask_document(document_id: str, payload: AskRequest, current_user: dict = Depends(get_current_user)) -> dict:
    document = store.find("documents", id=document_id, user_id=current_user["id"])
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    if document["status"] != "ready":
        raise HTTPException(status_code=400, detail="Document is not ready for questions.")
    return build_answer(current_user["id"], document_id, payload.question)


@router.get("/{document_id}/chat-history")
def chat_history(document_id: str, current_user: dict = Depends(get_current_user)) -> list[dict]:
    document = store.find("documents", id=document_id, user_id=current_user["id"])
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    return store.filter("chat_messages", user_id=current_user["id"], document_id=document_id)
