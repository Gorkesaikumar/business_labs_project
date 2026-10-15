from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class IngestionRunRequest(BaseModel):
    max_pages: Optional[int] = Field(default=20, ge=1, le=500)
    force_resync: Optional[bool] = Field(default=False)


class IngestionRunResponse(BaseModel):
    run_id: str
    status: str
    total_discovered: int
    added: int
    updated: int
    unchanged: int
    removed: int
    errors: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    summary: Dict[str, Any] = Field(default_factory=dict)
