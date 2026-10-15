from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    article_id: str
    url: str
    title: str
    heading: str = ""
    passage: str
    relevance_score: float
    screenshot_urls: List[str] = Field(default_factory=list)


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000, description="Product question to answer")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional caller context (e.g. email or meeting)")
    top_k: Optional[int] = Field(default=5, ge=1, le=20)
    threshold: Optional[float] = Field(default=0.60, ge=0.0, le=1.0)


class QueryResponse(BaseModel):
    request_id: str
    question: str
    answer: str
    status: str = Field(..., description="'answered', 'insufficient_evidence', or 'escalated'")
    sources: List[SourceCitation] = Field(default_factory=list)
    evidence_sufficiency: str = Field(..., description="'sufficient', 'partial', or 'insufficient'")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    requires_human: bool = False
    escalation_id: Optional[str] = None
    processing_time_ms: float
    model: str
