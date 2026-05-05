from app.services.quiz_generator import _update_weak_topic
from app.storage import store


def test_weak_topic_update_records_accuracy() -> None:
    user = store.insert("users", {"name": "Test User", "email": "test@example.com", "hashed_password": "x"})
    _update_weak_topic(user["id"], "RAG", False)
    _update_weak_topic(user["id"], "RAG", True)

    topic = store.find("weak_topics", user_id=user["id"], topic="RAG")
    assert topic["correct_count"] == 1
    assert topic["incorrect_count"] == 1
    assert topic["accuracy"] == 50.0
