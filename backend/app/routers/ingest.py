from fastapi import APIRouter, HTTPException

from app.schemas import (
    IngestResponse,
    IngestTextRequest,
    IngestURLRequest,
    KnowledgeBaseResponse,
    DocumentSummary,
)
from app.services import rag
from app.services.vector_store import get_vector_store

router = APIRouter(tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse)
def ingest_url_endpoint(req: IngestURLRequest) -> IngestResponse:
    try:
        res = rag.ingest_url(req.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")
    return IngestResponse(**res.__dict__)


@router.post("/ingest/text", response_model=IngestResponse)
def ingest_text_endpoint(req: IngestTextRequest) -> IngestResponse:
    try:
        res = rag.ingest_text(req.title, req.text, req.source)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")
    return IngestResponse(**res.__dict__)


@router.get("/knowledge-base", response_model=KnowledgeBaseResponse)
def list_kb() -> KnowledgeBaseResponse:
    store = get_vector_store()
    docs = store.list_documents()
    return KnowledgeBaseResponse(
        documents=[DocumentSummary(**d) for d in docs],
        total_chunks=store.size,
    )


@router.delete("/knowledge-base")
def reset_kb() -> dict:
    get_vector_store().reset()
    return {"status": "ok", "message": "Knowledge base cleared."}
