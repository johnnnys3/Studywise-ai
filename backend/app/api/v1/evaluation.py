from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.storage import store


router = APIRouter()


class MetricLogRequest(BaseModel):
    document_id: str | None = None
    metric_name: str
    metric_value: float
    metadata_json: dict = {}


@router.get("/metrics")
def metrics(current_user: dict = Depends(get_current_user)) -> list[dict]:
    existing = store.filter("evaluation_metrics", user_id=current_user["id"])
    if existing:
        return existing
    defaults = [
        ("retrieval_accuracy", 0),
        ("citation_coverage", 0),
        ("answer_groundedness", 0),
        ("average_response_time", 0),
        ("quiz_generation_success_rate", 0),
        ("json_validation_success_rate", 0),
        ("valid_source_page_rate", 0),
        ("difficulty_validation_pass_rate", 0),
        ("weak_topic_improvement_rate", 0),
    ]
    return [
        {
            "id": metric_name,
            "user_id": current_user["id"],
            "document_id": None,
            "metric_name": metric_name,
            "metric_value": value,
            "metadata_json": {},
        }
        for metric_name, value in defaults
    ]


@router.get("/rag-traces")
def rag_traces(current_user: dict = Depends(get_current_user)) -> list[dict]:
    traces = store.filter("rag_traces", user_id=current_user["id"])
    return sorted(traces, key=lambda item: item["created_at"], reverse=True)[:50]


@router.post("/log")
def log_metric(payload: MetricLogRequest, current_user: dict = Depends(get_current_user)) -> dict:
    return store.insert(
        "evaluation_metrics",
        {
            "user_id": current_user["id"],
            "document_id": payload.document_id,
            "metric_name": payload.metric_name,
            "metric_value": payload.metric_value,
            "metadata_json": payload.metadata_json,
        },
    )
