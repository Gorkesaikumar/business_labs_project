from typing import Dict, Any, List
from app.schemas import ScopeOfWorkSchema, RequirementSchema


class ScopeAgent:
    def generate_scope_of_work(
        self,
        analysis_data: Dict[str, Any],
        evaluated_requirements: List[RequirementSchema],
        version: int = 1,
    ) -> ScopeOfWorkSchema:
        project_id = analysis_data["project_id"]
        objective = analysis_data["project_objective"]
        current_problem = analysis_data["current_problem"]
        exclusions = analysis_data.get("exclusions", [])

        # Formulate structured deliverables from confirmed requirements
        deliverables = []
        for req in evaluated_requirements:
            deliverables.append({
                "deliverable_id": f"del_{req.id}",
                "title": req.title,
                "description": req.description,
                "feasibility_category": req.feasibility_classification,
                "acceptance_criteria": req.acceptance_criteria,
                "technical_approach": (
                    "Standard Admin Panel Configuration"
                    if req.feasibility_classification == "existing_configuration"
                    else "Frontend Widget Customization & Head Script Injection"
                    if req.feasibility_classification == "existing_with_limitations"
                    else "Bespoke API / Microservice Integration"
                ),
            })

        assumptions = [
            "Client will provide timely access to Brilliant Directories administrator credentials and DNS control panel.",
            "Production database currently holds valid geocoded addresses for existing member profiles.",
            "Third-party API credentials (Google Maps, Stripe, OpenAI/Anthropic) will be supplied by client.",
        ]

        dependencies = [
            "Brilliant Directories API v2 active license.",
            "Valid Google Maps Geocoding & Places API key with enabled billing.",
            "Stripe account verified for connected transactions.",
        ]

        client_responsibilities = [
            "Approve milestone deliverables within 3 business days of presentation.",
            "Supply verified CSV member data or category hierarchy mappings.",
            "Designate Sarah Miller as the sole authoritative product sign-off contact.",
        ]

        risks = [
            "Google Geocoding API rate limits during bulk address lookups.",
            "Browser permission denial for HTML5 geolocation on client devices.",
            "Timeline compression risk if client feedback cycles exceed 3 business days.",
        ]

        open_questions = [
            "Should unverified member profiles be completely hidden or merely deprioritized in search results?",
            "What is the client's preferred fallback if a user denies browser location access?",
        ]

        return ScopeOfWorkSchema(
            project_id=project_id,
            project_name=analysis_data.get("transcript_id", "Directory Project"),
            version=version,
            project_objective=objective,
            current_problem=current_problem,
            confirmed_requirements=evaluated_requirements,
            deliverables=deliverables,
            exclusions=exclusions,
            assumptions=assumptions,
            dependencies=dependencies,
            client_responsibilities=client_responsibilities,
            risks=risks,
            open_questions=open_questions,
        )
