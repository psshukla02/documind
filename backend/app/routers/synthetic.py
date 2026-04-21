from fastapi import APIRouter, HTTPException

from app.core.metrics import get_metrics
from app.schemas import SyntheticRequest, SyntheticResponse
from app.services import rag

router = APIRouter(tags=["synthetic"])


@router.post("/synthetic-data", response_model=SyntheticResponse)
def synthetic_endpoint(req: SyntheticRequest) -> SyntheticResponse:
    try:
        res = rag.generate_synthetic(req.doc_id, n_pairs=req.n_pairs)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        get_metrics().bump("errors")
        raise HTTPException(status_code=500, detail=f"Synthetic generation failed: {e}")
    return SyntheticResponse(**res)
