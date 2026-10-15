import uuid
import hashlib
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.knowledge import Escalation, Article, Chunk
from retrieval.vector_service import compute_deterministic_embedding


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EscalationService:
    @staticmethod
    async def create_escalation(
        db: AsyncSession,
        question: str,
        reason: str,
        context: Optional[Dict[str, Any]] = None,
        retrieval_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Escalation:
        escalation = Escalation(
            id=f"esc_{uuid.uuid4().hex[:12]}",
            question=question,
            context=context,
            retrieval_results=retrieval_results,
            reason=reason,
            status="pending",
            created_at=utcnow(),
        )
        db.add(escalation)
        await db.commit()
        await db.refresh(escalation)
        return escalation

    @staticmethod
    async def get_escalation(db: AsyncSession, escalation_id: str) -> Optional[Escalation]:
        stmt = select(Escalation).where(Escalation.id == escalation_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_escalations(
        db: AsyncSession,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Escalation]:
        stmt = select(Escalation)
        if status:
            stmt = stmt.where(Escalation.status == status)
        stmt = stmt.order_by(Escalation.created_at.desc()).limit(limit)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def resolve_escalation(
        db: AsyncSession,
        escalation_id: str,
        expert_answer: str,
        approved_by: str,
        supporting_evidence: Optional[str] = None,
    ) -> Optional[Escalation]:
        stmt = select(Escalation).where(Escalation.id == escalation_id)
        res = await db.execute(stmt)
        esc = res.scalar_one_or_none()
        if not esc:
            return None

        esc.status = "resolved"
        esc.expert_answer = expert_answer
        esc.supporting_evidence = supporting_evidence
        esc.approved_by = approved_by
        esc.resolved_at = utcnow()

        # Convert approved expert answer into an active knowledge article and searchable chunk
        article_id = f"art_expert_{esc.id}"
        article_url = f"https://support.brilliantdirectories.com/support/expert-answers/{esc.id}"
        content_text = f"Expert Resolution for: {esc.question}\n\nAnswer: {expert_answer}"
        if supporting_evidence:
            content_text += f"\n\nSupporting Evidence: {supporting_evidence}"

        content_hash = hashlib.sha256(content_text.encode()).hexdigest()

        # Check if article already exists
        art_stmt = select(Article).where(Article.id == article_id)
        art_res = await db.execute(art_stmt)
        existing_art = art_res.scalar_one_or_none()

        if not existing_art:
            new_art = Article(
                id=article_id,
                url=article_url,
                canonical_url=article_url,
                title=f"Expert Answer: {esc.question[:60]}",
                content=content_text,
                headings=[{"level": 1, "text": "Expert Resolution", "id": "resolution"}],
                tables=[],
                category="Expert Verified Answers",
                content_hash=content_hash,
                version=1,
                is_active=True,
                created_at=utcnow(),
                updated_at=utcnow(),
            )
            db.add(new_art)

            # Add searchable chunk with embedding
            chunk_embedding = compute_deterministic_embedding(content_text)
            chunk = Chunk(
                id=f"{article_id}_chunk_0",
                article_id=article_id,
                chunk_index=0,
                heading_path="Expert Resolution",
                content=content_text,
                token_count=len(content_text.split()),
                embedding_json=chunk_embedding,
                created_at=utcnow(),
            )
            db.add(chunk)

        await db.commit()
        await db.refresh(esc)
        return esc
