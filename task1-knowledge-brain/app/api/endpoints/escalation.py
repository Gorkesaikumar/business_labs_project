from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.api.deps import verify_admin_key
from app.schemas.escalation import EscalationCreateRequest, EscalationResolveRequest, EscalationResponse
from escalation.escalation_service import EscalationService

router = APIRouter()


@router.get("/escalations", response_model=List[EscalationResponse], summary="List human escalation tickets")
async def list_escalations(
    status: Optional[str] = Query(None, description="Filter by status: pending, resolved, rejected"),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    escalations = await EscalationService.list_escalations(db=db, status=status, limit=limit)
    return [
        EscalationResponse(
            id=e.id,
            question=e.question,
            reason=e.reason,
            status=e.status,
            expert_answer=e.expert_answer,
            supporting_evidence=e.supporting_evidence,
            approved_by=e.approved_by,
            created_at=e.created_at,
            resolved_at=e.resolved_at,
        )
        for e in escalations
    ]


@router.post("/escalations", response_model=EscalationResponse, summary="Create an escalation ticket")
async def create_escalation(
    request: EscalationCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    esc = await EscalationService.create_escalation(
        db=db,
        question=request.question,
        reason=request.reason,
        context=request.context,
        retrieval_results=request.retrieval_results,
    )
    return EscalationResponse(
        id=esc.id,
        question=esc.question,
        reason=esc.reason,
        status=esc.status,
        expert_answer=esc.expert_answer,
        supporting_evidence=esc.supporting_evidence,
        approved_by=esc.approved_by,
        created_at=esc.created_at,
        resolved_at=esc.resolved_at,
    )


@router.post("/escalations/{escalation_id}/resolve", response_model=EscalationResponse, summary="Resolve escalation and index expert answer")
async def resolve_escalation(
    escalation_id: str,
    request: EscalationResolveRequest,
    authenticated: bool = Depends(verify_admin_key),
    db: AsyncSession = Depends(get_db),
):
    resolved = await EscalationService.resolve_escalation(
        db=db,
        escalation_id=escalation_id,
        expert_answer=request.expert_answer,
        supporting_evidence=request.supporting_evidence,
        approved_by=request.approved_by,
    )
    if not resolved:
        raise HTTPException(status_code=404, detail=f"Escalation ticket {escalation_id} not found.")

    return EscalationResponse(
        id=resolved.id,
        question=resolved.question,
        reason=resolved.reason,
        status=resolved.status,
        expert_answer=resolved.expert_answer,
        supporting_evidence=resolved.supporting_evidence,
        approved_by=resolved.approved_by,
        created_at=resolved.created_at,
        resolved_at=resolved.resolved_at,
    )
