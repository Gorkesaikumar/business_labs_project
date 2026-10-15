import pytest
from app.schemas import RequirementSchema
from agents.scope_agent import ScopeAgent
from agents.estimation_agent import EstimationAgent
from agents.proposal_agent import ProposalAgent
from agents.scope_diff_agent import ScopeDiffAgent


def test_scope_diff_meeting_a_vs_meeting_c():
    scope_agent = ScopeAgent()
    estimation_agent = EstimationAgent()
    proposal_agent = ProposalAgent(hourly_rate=150.0)
    diff_agent = ScopeDiffAgent()

    # Meeting A Baseline Requirements
    reqs_a = [
        RequirementSchema(
            id="req_a_001",
            project_id="proj_metro",
            title="Multi-category Faceted Filtering",
            description="Filter by specialty and availability.",
            source_passage="Meeting A quote",
            speaker="Tom Chen",
        ),
        RequirementSchema(
            id="req_a_002",
            project_id="proj_metro",
            title="Zip Code Radius Distance Search",
            description="5 to 50 mile slider.",
            source_passage="Meeting A quote",
            speaker="Tom Chen",
        ),
    ]

    analysis_a = {
        "project_id": "proj_metro",
        "project_objective": "Metro Search v1",
        "current_problem": "Problem A",
        "exclusions": ["No iOS app"],
    }
    scope_a = scope_agent.generate_scope_of_work(analysis_a, reqs_a, version=1)
    tasks_a = estimation_agent.estimate_tasks(reqs_a)
    proposal_a = proposal_agent.generate_proposal(scope_a, tasks_a, timeline_weeks=6, version=1)

    # Meeting C Follow-up Requirements (Drops req_a_002, Adds req_c_001 AI Search)
    reqs_c = [
        RequirementSchema(
            id="req_a_001",
            project_id="proj_metro",
            title="Multi-category Faceted Filtering",
            description="Filter by specialty and availability.",
            source_passage="Meeting A quote",
            speaker="Tom Chen",
        ),
        RequirementSchema(
            id="req_c_001",
            project_id="proj_metro",
            title="AI Conversational Natural Language Search Assistant",
            description="Natural language queries against directory embeddings.",
            source_passage="Meeting C quote",
            speaker="Sarah Miller",
        ),
    ]

    analysis_c = {
        "project_id": "proj_metro",
        "project_objective": "Metro Search v2 with AI",
        "current_problem": "Problem C",
        "exclusions": ["No iOS app", "Dropped Zip Code Radius Slider"],
    }
    scope_c = scope_agent.generate_scope_of_work(analysis_c, reqs_c, version=2)
    tasks_c = estimation_agent.estimate_tasks(reqs_c)
    proposal_c = proposal_agent.generate_proposal(scope_c, tasks_c, timeline_weeks=4, version=2)

    # Execute Diff
    diff = diff_agent.compare_proposals(baseline_proposal=proposal_a, revised_proposal=proposal_c)

    # Verify Added Requirement
    assert len(diff.added_requirements) == 1
    assert diff.added_requirements[0].id == "req_c_001"

    # Verify Removed Requirement
    assert len(diff.removed_requirements) == 1
    assert diff.removed_requirements[0].id == "req_a_002"

    # Verify Unchanged Requirement
    assert len(diff.unchanged_requirements) == 1
    assert diff.unchanged_requirements[0].id == "req_a_001"

    # Verify Timeline Compression
    assert diff.timeline_baseline_weeks == 6
    assert diff.timeline_revised_weeks == 4
    assert diff.timeline_delta_weeks == -2

    # Verify Out-of-Scope and Schedule Compression Flags
    assert any("OUT_OF_SCOPE_API" in flag for flag in diff.out_of_scope_flags)
    assert any("SCHEDULE_COMPRESSION_RISK" in flag for flag in diff.out_of_scope_flags)

    # Verify Baseline proposal remains unchanged (immutable)
    assert proposal_a.version == 1
    assert proposal_a.timeline_weeks == 6
    assert len(proposal_a.scope_of_work.confirmed_requirements) == 2
