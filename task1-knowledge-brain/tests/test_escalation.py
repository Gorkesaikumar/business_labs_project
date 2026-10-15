import pytest
from escalation.escalation_service import EscalationService
from retrieval.vector_service import VectorService
from app.models.knowledge import Escalation, Article, Chunk
from sqlalchemy import select


@pytest.mark.asyncio
async def test_escalation_lifecycle_and_indexing(test_db):
    # 1. Create escalation
    esc = await EscalationService.create_escalation(
        db=test_db,
        question="Can I integrate Apple Pay directly into checkout?",
        reason="No specific documentation found for Apple Pay direct gateway.",
        context={"user_email": "client@example.com"},
    )

    assert esc.id.startswith("esc_")
    assert esc.status == "pending"

    # 2. List escalations
    pending = await EscalationService.list_escalations(db=test_db, status="pending")
    assert len(pending) == 1
    assert pending[0].id == esc.id

    # 3. Resolve escalation with human expert answer
    expert_answer = "Yes, Apple Pay is supported automatically via Stripe Elements when Stripe is enabled."
    resolved = await EscalationService.resolve_escalation(
        db=test_db,
        escalation_id=esc.id,
        expert_answer=expert_answer,
        approved_by="Lead Directory Architect",
        supporting_evidence="Stripe Elements docs v2.4",
    )

    assert resolved.status == "resolved"
    assert resolved.expert_answer == expert_answer
    assert resolved.approved_by == "Lead Directory Architect"
    assert resolved.resolved_at is not None

    # 4. Verify indexed article and chunk exist in DB
    art_stmt = select(Article).where(Article.id == f"art_expert_{esc.id}")
    art_res = await test_db.execute(art_stmt)
    indexed_art = art_res.scalar_one_or_none()
    assert indexed_art is not None
    assert "Apple Pay" in indexed_art.content

    # 5. Verify vector search finds the resolved knowledge
    vector_service = VectorService()
    search_results = await vector_service.search(
        db=test_db,
        query="Does Brilliant Directories support Apple Pay?",
        threshold=0.3,
    )
    assert len(search_results) >= 1
    assert search_results[0]["article_id"] == indexed_art.id
