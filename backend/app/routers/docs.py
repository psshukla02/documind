from fastapi import APIRouter, HTTPException

from app.core.metrics import get_metrics
from app.schemas import DocsRequest, DocsResponse
from app.services import rag

router = APIRouter(tags=["docs"])


@router.post("/generate-docs", response_model=DocsResponse)
def generate_docs_endpoint(req: DocsRequest) -> DocsResponse:
    try:
        res = rag.generate_documentation(req.topic, code=req.code, use_retrieval=req.use_retrieval)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        get_metrics().bump("errors")
        raise HTTPException(status_code=500, detail=f"Doc generation failed: {e}")
    return DocsResponse(**res)
