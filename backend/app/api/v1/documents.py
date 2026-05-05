from pathlib import Path
import re
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.services.chunker import semantic_chunk_pages
from app.services.document_parser import extract_text
from app.services.proposition_extractor import extract_chunk_propositions
from app.services.text_cleaner import remove_repeated_page_artifacts
from app.services.vector_store import upsert_document_chunks
from app.storage import store


router = APIRouter()
ALLOWED_SUFFIXES = {".pdf", ".txt"}
ALLOWED_TYPES = {"application/pdf", "text/plain"}


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name
    return re.sub(r"[^a-zA-Z0-9._-]", "_", name)


def serialize_document(document: dict) -> dict:
    chunks = store.filter("document_chunks", document_id=document["id"], user_id=document["user_id"])
    return {**document, "chunk_count": len(chunks)}


@router.post("", status_code=status.HTTP_201_CREATED)
def upload_document(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)) -> dict:
    settings = get_settings()
    original_filename = sanitize_filename(file.filename or "upload")
    suffix = Path(original_filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES or file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a PDF or TXT file.")

    user_upload_dir = settings.upload_path / current_user["id"]
    user_upload_dir.mkdir(parents=True, exist_ok=True)
    stored_filename = f"{uuid4().hex}{suffix}"
    stored_path = user_upload_dir / stored_filename

    size = 0
    with stored_path.open("wb") as output:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            if size > settings.max_upload_size_mb * 1024 * 1024:
                stored_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="File is too large for the MVP upload limit.")
            output.write(chunk)

    if size == 0:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Empty files cannot be processed.")

    document = store.insert(
        "documents",
        {
            "user_id": current_user["id"],
            "title": Path(original_filename).stem,
            "original_filename": original_filename,
            "file_type": suffix.replace(".", "").upper(),
            "file_path": str(stored_path),
            "status": "processing",
            "error_message": None,
            "total_pages": 0,
        },
    )

    try:
        pages = remove_repeated_page_artifacts(extract_text(stored_path, file.content_type))
        if not pages:
            raise ValueError("No readable text was found in the document.")
        stored_chunks = []
        for chunk in semantic_chunk_pages(pages):
            stored_chunk = store.insert(
                "document_chunks",
                {
                    "document_id": document["id"],
                    "user_id": current_user["id"],
                    "chunk_index": chunk.chunk_index,
                    "chunk_text": chunk.chunk_text,
                    "page_number": chunk.page_number,
                    "page_start": chunk.page_start or chunk.page_number,
                    "page_end": chunk.page_end or chunk.page_number,
                    "section_title": chunk.section_title,
                    "section_path_json": chunk.section_path or [],
                    "content_type": chunk.content_type,
                    "token_count": chunk.token_count,
                    "quality_score": chunk.quality_score,
                    "text_hash": chunk.text_hash,
                    "vector_id": f"chroma:{document['id']}:{chunk.chunk_index}",
                },
            )
            stored_chunks.append(stored_chunk)
        if not stored_chunks:
            raise ValueError("No high-quality study chunks could be created from this document.")

        upsert_document_chunks(stored_chunks)
        proposition_count = 0
        for stored_chunk in stored_chunks:
            for proposition in extract_chunk_propositions(stored_chunk):
                store.insert("chunk_propositions", proposition)
                proposition_count += 1
        document = store.update(
            "documents",
            document["id"],
            {
                "status": "ready",
                "total_pages": len(pages),
                "error_message": None,
                "processing_summary_json": {
                    "chunk_count": len(stored_chunks),
                    "proposition_count": proposition_count,
                    "average_chunk_quality": round(
                        sum(float(chunk.get("quality_score", 0)) for chunk in stored_chunks) / len(stored_chunks),
                        3,
                    ),
                    "rag_architecture": "semantic_chunks_with_chroma_vector_index",
                },
            },
        )
    except Exception as exc:
        document = store.update("documents", document["id"], {"status": "failed", "error_message": str(exc)})

    return serialize_document(document)


@router.get("")
def list_documents(current_user: dict = Depends(get_current_user)) -> list[dict]:
    documents = store.filter("documents", user_id=current_user["id"])
    return [serialize_document(document) for document in sorted(documents, key=lambda item: item["created_at"], reverse=True)]


@router.get("/{document_id}")
def get_document(document_id: str, current_user: dict = Depends(get_current_user)) -> dict:
    document = store.find("documents", id=document_id, user_id=current_user["id"])
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    chunks = store.filter("document_chunks", document_id=document_id, user_id=current_user["id"])
    return {**serialize_document(document), "chunks": chunks[:8]}


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, current_user: dict = Depends(get_current_user)) -> None:
    document = store.find("documents", id=document_id, user_id=current_user["id"])
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    path = Path(document["file_path"])
    if path.exists():
        path.unlink()
    store.delete("documents", document_id)
