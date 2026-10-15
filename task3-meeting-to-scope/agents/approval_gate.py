from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.schemas import ProposalSchema


class ApprovalGateError(Exception):
    pass


class HumanApprovalGate:
    def approve_proposal(
        self,
        proposal: ProposalSchema,
        reviewer_name: str,
        comments: Optional[str] = None,
    ) -> ProposalSchema:
        """Record formal human review and approval for commercial proposal."""
        if not reviewer_name or len(reviewer_name.strip()) < 2:
            raise ApprovalGateError("Reviewer identity required to record commercial approval.")

        proposal.status = "approved"
        proposal.approved_by = reviewer_name.strip()
        proposal.approved_at = datetime.now(timezone.utc)
        return proposal

    def reject_proposal(
        self,
        proposal: ProposalSchema,
        reviewer_name: str,
        rejection_reason: str,
    ) -> ProposalSchema:
        """Record formal rejection."""
        if not rejection_reason:
            raise ApprovalGateError("Rejection reason required.")
        proposal.status = "rejected"
        proposal.approved_by = reviewer_name.strip()
        proposal.approved_at = datetime.now(timezone.utc)
        return proposal

    def verify_can_send(self, proposal: ProposalSchema) -> bool:
        """Enforces that an unapproved proposal CANNOT be dispatched to client."""
        if proposal.status != "approved":
            raise ApprovalGateError(
                f"Commercial Proposal '{proposal.proposal_id}' (v{proposal.version}) has status '{proposal.status}'. "
                f"Backend security policy strictly forbids dispatching proposals without verified human approval."
            )
        if not proposal.approved_by or not proposal.approved_at:
            raise ApprovalGateError("Missing authoritative reviewer signature.")
        return True
