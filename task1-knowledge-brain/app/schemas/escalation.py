from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class EscalationCreateRequest(BaseModel):
    question: str = Field(..., min_length=3)
    reason: str = Field(..., description="Why automated answer was insufficient")
    context: Optional[Dict[str, Any]] = None
    retrieval_results: Optional[List[Dict[str, Any]]] = None


class EscalationResolveRequest(BaseModel):
    expert_answer: str = Field(..., min_length=10)
    supporting_evidence: Optional[str] = None
    approved_by: str = Field(..., min_length=2)


class EscalationResponse(BaseModel):
    id: str
    question: str
    reason: str
    status: str
    expert_answer: Optional[str] = None
    supporting_evidence: Optional[str] = None
    approved_by: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
