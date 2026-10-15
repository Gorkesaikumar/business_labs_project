import pytest
from app.schemas import RequirementSchema
from agents.feasibility_agent import ProductFeasibilityAgent


@pytest.mark.asyncio
async def test_feasibility_classifications():
    agent = ProductFeasibilityAgent()

    # 1. Native Stripe checkout
    req_stripe = RequirementSchema(
        id="req_test_1",
        project_id="proj_1",
        title="Stripe Payment Gateway",
        description="Connect Stripe credit cards.",
        source_passage="Speaker quote",
        speaker="Client",
    )
    res_stripe = await agent.evaluate_requirement(req_stripe)
    assert res_stripe.feasibility_classification == "existing_configuration"

    # 2. AI semantic search
    req_ai = RequirementSchema(
        id="req_test_2",
        project_id="proj_1",
        title="AI Conversational Search Bar",
        description="Natural language queries against vector embeddings.",
        source_passage="Speaker quote",
        speaker="Client",
    )
    res_ai = await agent.evaluate_requirement(req_ai)
    assert res_ai.feasibility_classification == "potential_custom_development"

    # 3. Faceted filtering UI
    req_facet = RequirementSchema(
        id="req_test_3",
        project_id="proj_1",
        title="Faceted Filter Sidebar",
        description="Multi-category checkboxes with dynamic slide-out drawer.",
        source_passage="Speaker quote",
        speaker="Client",
    )
    res_facet = await agent.evaluate_requirement(req_facet)
    assert res_facet.feasibility_classification == "existing_with_limitations"
