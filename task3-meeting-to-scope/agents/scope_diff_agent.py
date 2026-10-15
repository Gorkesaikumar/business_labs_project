from typing import Dict, Any, List
from app.schemas import ProposalSchema, ScopeDiffSchema, RequirementSchema


class ScopeDiffAgent:
    def compare_proposals(
        self,
        baseline_proposal: ProposalSchema,
        revised_proposal: ProposalSchema,
    ) -> ScopeDiffSchema:
        """Compare revised follow-up proposal against approved baseline proposal."""
        baseline_reqs: Dict[str, RequirementSchema] = {
            r.id: r for r in baseline_proposal.scope_of_work.confirmed_requirements
        }
        revised_reqs: Dict[str, RequirementSchema] = {
            r.id: r for r in revised_proposal.scope_of_work.confirmed_requirements
        }

        added: List[RequirementSchema] = []
        removed: List[RequirementSchema] = []
        modified: List[Dict[str, Any]] = []
        unchanged: List[RequirementSchema] = []

        # Find added and modified
        for req_id, r_rev in revised_reqs.items():
            if req_id not in baseline_reqs:
                added.append(r_rev)
            else:
                r_base = baseline_reqs[req_id]
                if (
                    r_base.title != r_rev.title
                    or r_base.description != r_rev.description
                    or r_base.priority != r_rev.priority
                ):
                    modified.append({
                        "requirement_id": req_id,
                        "title_before": r_base.title,
                        "title_after": r_rev.title,
                        "description_before": r_base.description,
                        "description_after": r_rev.description,
                        "priority_before": r_base.priority,
                        "priority_after": r_rev.priority,
                    })
                else:
                    unchanged.append(r_rev)

        # Find removed
        for req_id, r_base in baseline_reqs.items():
            if req_id not in revised_reqs:
                removed.append(r_base)

        hours_delta = revised_proposal.total_hours_likely - baseline_proposal.total_hours_likely
        cost_delta = revised_proposal.estimated_cost_likely - baseline_proposal.estimated_cost_likely
        timeline_delta = revised_proposal.timeline_weeks - baseline_proposal.timeline_weeks

        # Detect out-of-scope risks
        out_of_scope_flags = []
        for a in added:
            if "ai conversational" in a.title.lower():
                out_of_scope_flags.append(
                    "OUT_OF_SCOPE_API: AI Conversational Search requires external vector embedding infrastructure and LLM token budget not present in native BD hosting."
                )
        if timeline_delta < 0:
            out_of_scope_flags.append(
                f"SCHEDULE_COMPRESSION_RISK: Delivery timeline compressed by {abs(timeline_delta)} weeks (from {baseline_proposal.timeline_weeks}w to {revised_proposal.timeline_weeks}w). Requires dedicated sprint allocation."
            )

        human_summary = (
            f"Scope Delta Report for Project '{baseline_proposal.project_id}' (v{baseline_proposal.version} -> v{revised_proposal.version}):\n\n"
            f"1. Added Requirements ({len(added)}):\n"
            + "\n".join([f"   + [{a.id}] {a.title}: {a.description}" for a in added])
            + f"\n\n2. Removed Requirements ({len(removed)}):\n"
            + "\n".join([f"   - [{r.id}] {r.title}: Dropped per client strategic update." for r in removed])
            + f"\n\n3. Unchanged Requirements ({len(unchanged)}):\n"
            + "\n".join([f"   = [{u.id}] {u.title}" for u in unchanged])
            + f"\n\n4. Commercial Impact:\n"
            f"   - Timeline: {baseline_proposal.timeline_weeks} weeks -> {revised_proposal.timeline_weeks} weeks ({timeline_delta:+d} weeks)\n"
            f"   - Engineering Effort: {baseline_proposal.total_hours_likely:.1f} hrs -> {revised_proposal.total_hours_likely:.1f} hrs ({hours_delta:+.1f} hrs)\n"
            f"   - Estimated Cost: ${baseline_proposal.estimated_cost_likely:,.2f} -> ${revised_proposal.estimated_cost_likely:,.2f} ({cost_delta:+,.2f})\n\n"
            f"5. Critical Alerts & Out-of-Scope Flags:\n"
            + "\n".join([f"   ! {flag}" for flag in out_of_scope_flags])
        )

        return ScopeDiffSchema(
            project_id=baseline_proposal.project_id,
            baseline_version=baseline_proposal.version,
            revised_version=revised_proposal.version,
            added_requirements=added,
            removed_requirements=removed,
            modified_requirements=modified,
            unchanged_requirements=unchanged,
            timeline_baseline_weeks=baseline_proposal.timeline_weeks,
            timeline_revised_weeks=revised_proposal.timeline_weeks,
            timeline_delta_weeks=timeline_delta,
            hours_delta_likely=hours_delta,
            cost_delta_likely=cost_delta,
            out_of_scope_flags=out_of_scope_flags,
            human_summary=human_summary,
        )
