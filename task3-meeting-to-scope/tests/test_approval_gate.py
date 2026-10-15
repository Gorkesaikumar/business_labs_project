import pytest
from agents.approval_gate import HumanApprovalGate, ApprovalGateError
from agents.proposal_agent import ProposalAgent
from agents.scope_agent import ScopeAgent
from agents.estimation_agent import EstimationAgent


def test_human_approval_gate_enforcement():
    gate = HumanApprovalGate()
    scope_agent = ScopeAgent()
    estimation_agent = EstimationAgent()
    proposal_agent = ProposalAgent()

    scope = scope_agent.generate_scope_of_work(
        {"project_id": "p1", "project_objective": "Obj", "current_problem": "Prob", "exclusions": []},
        [],
    )
    proposal = proposal_agent.generate_proposal(scope, [], timeline_weeks=4)

    # 1. Proposal starts in draft status
    assert proposal.status == "draft"

    # 2. Attempting to send unapproved proposal MUST raise ApprovalGateError
    with pytest.raises(ApprovalGateError) as exc_info:
        gate.verify_can_send(proposal)
    assert "strictly forbids dispatching" in str(exc_info.value)

    # 3. Approve proposal
    approved = gate.approve_proposal(proposal, reviewer_name="Sarah Miller (Lead PO)")
    assert approved.status == "approved"
    assert approved.approved_by == "Sarah Miller (Lead PO)"
    assert approved.approved_at is not None

    # 4. Now sending is authorized
    assert gate.verify_can_send(approved) is True

    # 5. Rejection test
    proposal2 = proposal_agent.generate_proposal(scope, [], timeline_weeks=4)
    rejected = gate.reject_proposal(proposal2, reviewer_name="CFO", rejection_reason="Exceeds quarterly budget cap.")
    assert rejected.status == "rejected"
    with pytest.raises(ApprovalGateError):
        gate.verify_can_send(rejected)
