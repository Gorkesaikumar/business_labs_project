import pytest
from app.schemas import RequirementSchema
from agents.scope_agent import ScopeAgent
from agents.estimation_agent import EstimationAgent
from agents.proposal_agent import ProposalAgent


def test_scope_and_estimation_pipeline():
    scope_agent = ScopeAgent()
    estimation_agent = EstimationAgent()
    proposal_agent = ProposalAgent(hourly_rate=150.0)

    reqs = [
        RequirementSchema(
            id="req_test_1",
            project_id="proj_test",
            title="Faceted Search Filtering",
            description="Filter by specialty and availability.",
            source_passage="Quote",
            speaker="Client",
            feasibility_classification="existing_with_limitations",
            acceptance_criteria=["Filter updates results."],
        ),
        RequirementSchema(
            id="req_test_2",
            project_id="proj_test",
            title="Mobile Slide-Out Drawer",
            description="Mobile navigation drawer.",
            source_passage="Quote",
            speaker="Client",
            feasibility_classification="existing_with_limitations",
            acceptance_criteria=["Slide drawer works on mobile."],
        ),
    ]

    analysis = {
        "project_id": "proj_test",
        "project_objective": "Test Objective",
        "current_problem": "Test Problem",
        "exclusions": ["No iOS app"],
    }

    # 1. Generate SOW
    scope = scope_agent.generate_scope_of_work(analysis, reqs, version=1)
    assert len(scope.deliverables) == 2
    assert len(scope.exclusions) == 1
    assert len(scope.assumptions) >= 1

    # 2. Estimate Tasks
    tasks = estimation_agent.estimate_tasks(reqs)
    assert len(tasks) >= 3  # Feature tasks + QA task
    total_likely = sum(t.most_likely_hours for t in tasks)
    assert total_likely > 0

    # 3. Generate Proposal
    proposal = proposal_agent.generate_proposal(scope, tasks, timeline_weeks=6, version=1)
    assert proposal.status == "draft"
    assert proposal.total_hours_likely == total_likely
    assert proposal.estimated_cost_likely == total_likely * 150.0
    assert proposal.approved_by is None
