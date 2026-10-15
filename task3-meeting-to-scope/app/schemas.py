from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RequirementSchema(BaseModel):
    id: str
    project_id: str
    title: str
    description: str
    source_passage: str
    speaker: str
    status: str = Field(default="confirmed", description="'confirmed' or 'assumption'")
    priority: str = Field(default="medium", description="'low', 'medium', 'high', 'critical'")
    feasibility_classification: Optional[str] = Field(
        default=None,
        description="'existing_configuration', 'existing_with_limitations', 'potential_custom_development', 'needs_clarification'"
    )
    feasibility_evidence: Optional[str] = None
    acceptance_criteria: List[str] = Field(default_factory=list)
    is_active: bool = True
    change_type: Optional[str] = Field(default="unchanged", description="'added', 'removed', 'modified', 'unchanged'")


class TaskEstimateSchema(BaseModel):
    task_id: str
    requirement_ids: List[str]
    task_name: str
    low_hours: float
    most_likely_hours: float
    high_hours: float
    rationale: str
    assumptions: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    human_review_status: str = "pending"


class ScopeOfWorkSchema(BaseModel):
    project_id: str
    project_name: str
    version: int = 1
    project_objective: str
    current_problem: str
    confirmed_requirements: List[RequirementSchema]
    deliverables: List[Dict[str, Any]]
    exclusions: List[str]
    assumptions: List[str]
    dependencies: List[str]
    client_responsibilities: List[str]
    risks: List[str]
    open_questions: List[str]


class ProposalSchema(BaseModel):
    proposal_id: str
    project_id: str
    version: int = 1
    title: str
    executive_summary: str
    scope_of_work: ScopeOfWorkSchema
    task_estimates: List[TaskEstimateSchema]
    total_hours_low: float
    total_hours_likely: float
    total_hours_high: float
    hourly_rate: float = 150.0
    estimated_cost_low: float
    estimated_cost_likely: float
    estimated_cost_high: float
    timeline_weeks: int
    status: str = Field(default="draft", description="'draft', 'approved', 'rejected'")
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScopeDiffSchema(BaseModel):
    project_id: str
    baseline_version: int
    revised_version: int
    added_requirements: List[RequirementSchema]
    removed_requirements: List[RequirementSchema]
    modified_requirements: List[Dict[str, Any]]
    unchanged_requirements: List[RequirementSchema]
    timeline_baseline_weeks: int
    timeline_revised_weeks: int
    timeline_delta_weeks: int
    hours_delta_likely: float
    cost_delta_likely: float
    out_of_scope_flags: List[str]
    human_summary: str
