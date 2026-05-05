from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.storage import store


router = APIRouter()


@router.get("/summary")
def summary(current_user: dict = Depends(get_current_user)) -> dict:
    documents = store.filter("documents", user_id=current_user["id"])
    attempts = store.filter("quiz_attempts", user_id=current_user["id"])
    weak_topics = store.filter("weak_topics", user_id=current_user["id"])
    average_score = round(sum(attempt["percentage"] for attempt in attempts) / len(attempts), 1) if attempts else 0
    return {
        "total_documents": len(documents),
        "quizzes_completed": len(attempts),
        "average_quiz_score": average_score,
        "weak_topic_count": len([topic for topic in weak_topics if topic["accuracy"] < 70]),
        "recent_attempts": attempts[-5:],
    }


@router.get("/weak-topics")
def weak_topics(current_user: dict = Depends(get_current_user)) -> list[dict]:
    topics = store.filter("weak_topics", user_id=current_user["id"])
    return sorted(topics, key=lambda topic: topic["accuracy"])


@router.get("/recommendations")
def recommendations(current_user: dict = Depends(get_current_user)) -> list[dict]:
    topics = sorted(store.filter("weak_topics", user_id=current_user["id"]), key=lambda topic: topic["accuracy"])
    return [
        {
            "topic": topic["topic"],
            "message": topic.get("review_recommendation")
            or f"Review source material related to {topic['topic']} and retake a short quiz.",
            "priority": "high" if topic["accuracy"] < 50 else "medium",
            "document_id": topic.get("document_id"),
            "source_page": topic.get("source_page"),
            "source_chunk_id": topic.get("source_chunk_id"),
            "difficulty": topic.get("difficulty"),
            "cognitive_skill": topic.get("cognitive_skill"),
        }
        for topic in topics[:5]
    ]
