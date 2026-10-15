import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.schemas import ProposalSchema, ScopeDiffSchema, RequirementSchema
from agents.transcript_analyst import TranscriptAnalystAgent
from agents.feasibility_agent import ProductFeasibilityAgent
from agents.scope_agent import ScopeAgent
from agents.estimation_agent import EstimationAgent
from agents.proposal_agent import ProposalAgent
from agents.scope_diff_agent import ScopeDiffAgent
from agents.approval_gate import HumanApprovalGate, ApprovalGateError

app = FastAPI(
    title="Meeting to Scope of Work API",
    description="Multi-agent workflow converting transcripts to feasibility-checked scopes, estimates, and proposals.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyst_agent = TranscriptAnalystAgent()
feasibility_agent = ProductFeasibilityAgent()
scope_agent = ScopeAgent()
estimation_agent = EstimationAgent()
proposal_agent = ProposalAgent()
scope_diff_agent = ScopeDiffAgent()
approval_gate = HumanApprovalGate()

proposals_db: Dict[str, ProposalSchema] = {}

TRANSCRIPTS_DIR = Path(__file__).parent.parent.parent / "datasets" / "transcripts"


def load_transcript(transcript_id: str) -> Dict[str, Any]:
    file_map = {
        "trx_meeting_a": TRANSCRIPTS_DIR / "meeting_a.json",
        "trx_meeting_b": TRANSCRIPTS_DIR / "meeting_b.json",
        "trx_meeting_c": TRANSCRIPTS_DIR / "meeting_c.json",
    }
    path = file_map.get(transcript_id)
    if not path or not path.exists():
        raise HTTPException(status_code=404, detail=f"Transcript {transcript_id} not found.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/health", tags=["Health"])
async def health():
    return {
        "service": "Task 3: Meeting to Scope",
        "status": "healthy",
        "proposals_count": len(proposals_db),
    }


@app.get("/transcripts", tags=["Transcripts"])
async def list_transcripts():
    results = []
    for file_name in ["meeting_a.json", "meeting_b.json", "meeting_c.json"]:
        p = TRANSCRIPTS_DIR / file_name
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                results.append({
                    "transcript_id": data["transcript_id"],
                    "project_id": data["project_id"],
                    "project_name": data["project_name"],
                    "meeting_type": data["meeting_type"],
                    "participants_count": len(data["participants"]),
                })
    return results


@app.post("/transcripts/{transcript_id}/process", response_model=ProposalSchema, tags=["Pipeline"])
async def process_transcript(transcript_id: str):
    raw_data = load_transcript(transcript_id)

    # 1. Transcript Analyst
    analysis = analyst_agent.analyze_transcript(raw_data)

    # 2. Feasibility Agent
    evaluated_reqs = await feasibility_agent.evaluate_all(
        [RequirementSchema.model_validate(r) for r in analysis["requirements"]]
    )

    # 3. Scope Agent
    version = 2 if transcript_id == "trx_meeting_c" else 1
    scope = scope_agent.generate_scope_of_work(
        analysis_data=analysis,
        evaluated_requirements=evaluated_reqs,
        version=version,
    )

    # 4. Estimation Agent
    task_estimates = estimation_agent.estimate_tasks(evaluated_reqs)

    # 5. Proposal Agent
    proposal = proposal_agent.generate_proposal(
        scope=scope,
        tasks=task_estimates,
        timeline_weeks=analysis["timeline_weeks"],
        version=version,
    )

    proposals_db[proposal.proposal_id] = proposal
    return proposal


class ApprovalRequest(BaseModel):
    reviewer_name: str
    comments: Optional[str] = None


@app.post("/proposals/{proposal_id}/approve", response_model=ProposalSchema, tags=["Approvals"])
async def approve_proposal(proposal_id: str, request: ApprovalRequest):
    proposal = proposals_db.get(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found.")

    try:
        updated = approval_gate.approve_proposal(
            proposal=proposal,
            reviewer_name=request.reviewer_name,
            comments=request.comments,
        )
        proposals_db[proposal_id] = updated
        return updated
    except ApprovalGateError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/proposals/{proposal_id}/send", tags=["Approvals"])
async def send_proposal(proposal_id: str):
    """Enforces human approval check in backend business logic before dispatch."""
    proposal = proposals_db.get(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} not found.")

    try:
        approval_gate.verify_can_send(proposal)
        return {
            "status": "dispatched",
            "message": f"Proposal '{proposal.title}' successfully dispatched to client.",
            "approved_by": proposal.approved_by,
            "approved_at": proposal.approved_at,
        }
    except ApprovalGateError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@app.post("/proposals/diff", response_model=ScopeDiffSchema, tags=["Scope Diff"])
async def compare_proposals(baseline_id: str, revised_id: str):
    baseline = proposals_db.get(baseline_id)
    revised = proposals_db.get(revised_id)

    if not baseline or not revised:
        raise HTTPException(
            status_code=404,
            detail=f"Both baseline ({baseline_id}) and revised ({revised_id}) proposals must exist in store.",
        )

    diff = scope_diff_agent.compare_proposals(baseline, revised)
    return diff


@app.get("/proposals", response_model=List[ProposalSchema], tags=["Proposals"])
async def list_proposals():
    return list(proposals_db.values())
