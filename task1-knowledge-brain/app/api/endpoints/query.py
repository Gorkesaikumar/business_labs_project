from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.query import QueryRequest, QueryResponse
from retrieval.rag_pipeline import RAGPipeline

router = APIRouter()
rag_pipeline = RAGPipeline()


@router.post("/query", response_model=QueryResponse, summary="Query Knowledge Brain for grounded answers")
async def query_knowledge_brain(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
) -> QueryResponse:
    """Accepts a customer or project question, retrieves evidence chunks, evaluates sufficiency,
    and returns a strictly grounded Claude answer with verifiable source citations."""
    try:
        response = await rag_pipeline.answer_query(
            db=db,
            question=request.question,
            context=request.context,
            top_k=request.top_k,
            threshold=request.threshold,
        )
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Knowledge Brain query failed: {str(exc)}")
