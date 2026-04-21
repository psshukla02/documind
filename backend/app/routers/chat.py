from fastapi import APIRouter, HTTPException

from app.core.metrics import get_metrics
from app.schemas import ChatRequest, ChatResponse
from app.services import rag

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest) -> ChatResponse:
    try:
        res = rag.chat(req.query, top_k=req.top_k)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        get_metrics().bump("errors")
        raise HTTPException(status_code=500, detail=f"Chat failed: {e}")
    return ChatResponse(**res.__dict__)
