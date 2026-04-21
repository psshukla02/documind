from fastapi import APIRouter

from app.core.metrics import get_metrics
from app.schemas import HealthResponse, MetricsResponse
from app.services.llm import get_llm
from app.services.vector_store import get_vector_store

router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_model=MetricsResponse)
def metrics_endpoint() -> MetricsResponse:
    return MetricsResponse(**get_metrics().snapshot())


@router.get("/health", response_model=HealthResponse)
def health_endpoint() -> HealthResponse:
    llm = get_llm()
    return HealthResponse(
        status="ok",
        stub_mode=llm.stub_mode,
        vector_store_size=get_vector_store().size,
        model=llm.settings.openai_chat_model if not llm.stub_mode else "stub",
    )
