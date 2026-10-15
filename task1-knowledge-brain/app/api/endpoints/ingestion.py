import uuid
from datetime import datetime, timezone
from typing import Optional

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db, AsyncSessionLocal
from app.api.deps import verify_admin_key
from app.models.knowledge import IngestionRun, Article, Chunk
from app.schemas.ingestion import IngestionRunRequest, IngestionRunResponse
from ingestion.sitemap_crawler import SitemapCrawler
from retrieval.chunker import split_into_semantic_chunks
from retrieval.vector_service import compute_deterministic_embedding

router = APIRouter()


async def execute_ingestion_and_chunking(run_id: str, max_pages: int, force_resync: bool):
    """Background ingestion and chunk generation task."""
    async with AsyncSessionLocal() as db:
        crawler = SitemapCrawler(max_pages=max_pages)
        await crawler.run_crawl(db=db, run_id=run_id, force_resync=force_resync)

        # Generate chunks for newly crawled/updated active articles
        stmt = select(Article).where(Article.is_active == True)
        res = await db.execute(stmt)
        articles = res.scalars().all()

        for art in articles:
            # Check if chunks already exist
            chunk_stmt = select(Chunk).where(Chunk.article_id == art.id)
            c_res = await db.execute(chunk_stmt)
            existing_chunks = c_res.scalars().all()

            if not existing_chunks or force_resync:
                # Delete existing chunks if resync
                for ec in existing_chunks:
                    await db.delete(ec)
                await db.flush()

                new_chunks_data = split_into_semantic_chunks(
                    article_id=art.id,
                    article_url=art.url,
                    title=art.title,
                    content=art.content,
                    headings=art.headings or [],
                )
                for cd in new_chunks_data:
                    emb = compute_deterministic_embedding(cd["content"])
                    chunk = Chunk(
                        id=cd["id"],
                        article_id=cd["article_id"],
                        chunk_index=cd["chunk_index"],
                        heading_path=cd["heading_path"],
                        content=cd["content"],
                        token_count=cd["token_count"],
                        embedding_json=emb,
                    )
                    db.add(chunk)
                await db.commit()


@router.post("/ingestion/run", response_model=IngestionRunResponse, summary="Trigger crawler ingestion run")
async def trigger_ingestion_run(
    request: IngestionRunRequest,
    background_tasks: BackgroundTasks,
    authenticated: bool = Depends(verify_admin_key),
    db: AsyncSession = Depends(get_db),
) -> IngestionRunResponse:
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    crawler = SitemapCrawler(max_pages=request.max_pages)

    # For small batch (<= 20 pages), run synchronously so caller gets immediate accurate stats;
    # for larger crawls, background execution can be used.
    if request.max_pages and request.max_pages <= 20:
        run = await crawler.run_crawl(db=db, run_id=run_id, force_resync=request.force_resync)
        # Create chunks
        stmt = select(Article).where(Article.is_active == True)
        res = await db.execute(stmt)
        articles = res.scalars().all()

        for art in articles:
            chunk_stmt = select(Chunk).where(Chunk.article_id == art.id)
            c_res = await db.execute(chunk_stmt)
            existing_chunks = c_res.scalars().all()
            if not existing_chunks or request.force_resync:
                for ec in existing_chunks:
                    await db.delete(ec)
                await db.flush()
                new_chunks_data = split_into_semantic_chunks(
                    article_id=art.id,
                    article_url=art.url,
                    title=art.title,
                    content=art.content,
                    headings=art.headings or [],
                )
                for cd in new_chunks_data:
                    emb = compute_deterministic_embedding(cd["content"])
                    db.add(Chunk(
                        id=cd["id"],
                        article_id=cd["article_id"],
                        chunk_index=cd["chunk_index"],
                        heading_path=cd["heading_path"],
                        content=cd["content"],
                        token_count=cd["token_count"],
                        embedding_json=emb,
                    ))
                await db.commit()

        return IngestionRunResponse(
            run_id=run.id,
            status=run.status,
            total_discovered=run.total_discovered,
            added=run.added_count,
            updated=run.updated_count,
            unchanged=run.unchanged_count,
            removed=run.removed_count,
            errors=run.error_count,
            started_at=run.started_at,
            completed_at=run.completed_at,
            summary=run.summary,
        )
    else:
        background_tasks.add_task(
            execute_ingestion_and_chunking,
            run_id=run_id,
            max_pages=request.max_pages,
            force_resync=request.force_resync,
        )
        return IngestionRunResponse(
            run_id=run_id,
            status="running",
            total_discovered=request.max_pages,
            added=0,
            updated=0,
            unchanged=0,
            removed=0,
            errors=0,
            started_at=utcnow(),
            summary={"message": "Ingestion initiated in background."},
        )


@router.get("/ingestion/status", summary="Get latest ingestion status")
async def get_ingestion_status(db: AsyncSession = Depends(get_db)):
    stmt = select(IngestionRun).order_by(IngestionRun.started_at.desc()).limit(1)
    res = await db.execute(stmt)
    latest_run = res.scalar_one_or_none()
    if not latest_run:
        return {"status": "idle", "message": "No ingestion runs recorded yet."}
    return {
        "run_id": latest_run.id,
        "status": latest_run.status,
        "total_discovered": latest_run.total_discovered,
        "added": latest_run.added_count,
        "updated": latest_run.updated_count,
        "unchanged": latest_run.unchanged_count,
        "errors": latest_run.error_count,
        "started_at": latest_run.started_at,
        "completed_at": latest_run.completed_at,
        "summary": latest_run.summary,
    }
