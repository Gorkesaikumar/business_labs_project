import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
from app.schemas import ProposalSchema, ScopeOfWorkSchema, TaskEstimateSchema


class ProposalAgent:
    def __init__(self, hourly_rate: float = 150.0):
        self.hourly_rate = hourly_rate

    def generate_proposal(
        self,
        scope: ScopeOfWorkSchema,
        tasks: List[TaskEstimateSchema],
        timeline_weeks: int,
        version: int = 1,
    ) -> ProposalSchema:
        total_low = sum(t.low_hours for t in tasks)
        total_likely = sum(t.most_likely_hours for t in tasks)
        total_high = sum(t.high_hours for t in tasks)

        cost_low = total_low * self.hourly_rate
        cost_likely = total_likely * self.hourly_rate
        cost_high = total_high * self.hourly_rate

        exec_summary = (
            f"BusinessLabs Technical Consulting Proposal for {scope.project_name} (Version {version}).\n\n"
            f"Objective: {scope.project_objective}\n"
            f"Scope Summary: Delivery of {len(scope.deliverables)} technical deliverables across a {timeline_weeks}-week timeline. "
            f"Estimated total engineering effort: {total_likely:.1f} hours (${cost_likely:,.2f} at ${self.hourly_rate:.2f}/hr). "
            f"Strict scope boundaries and acceptance criteria are defined to prevent scope creep."
        )

        return ProposalSchema(
            proposal_id=f"prop_{uuid.uuid4().hex[:12]}",
            project_id=scope.project_id,
            version=version,
            title=f"Commercial Proposal: {scope.project_name} (v{version})",
            executive_summary=exec_summary,
            scope_of_work=scope,
            task_estimates=tasks,
            total_hours_low=total_low,
            total_hours_likely=total_likely,
            total_hours_high=total_high,
            hourly_rate=self.hourly_rate,
            estimated_cost_low=cost_low,
            estimated_cost_likely=cost_likely,
            estimated_cost_high=cost_high,
            timeline_weeks=timeline_weeks,
            status="draft",  # STRICTLY DRAFT until human approval is recorded!
            approved_by=None,
            approved_at=None,
            created_at=datetime.now(timezone.utc),
        )
