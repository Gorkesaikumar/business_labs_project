import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.db.session import init_db, AsyncSessionLocal
from app.api.endpoints import query, ingestion, escalation, health
from ingestion.sitemap_crawler import SitemapCrawler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("knowledge_brain")

scheduler = AsyncIOScheduler()


async def scheduled_daily_ingestion():
    """Daily incremental sitemap check as required by capstone specification."""
    logger.info("Executing scheduled daily incremental ingestion...")
    async with AsyncSessionLocal() as db:
        try:
            crawler = SitemapCrawler(max_pages=settings.CRAWL_MAX_PAGES)
            run = await crawler.run_crawl(db=db, run_id=f"daily_{int(asyncio.get_event_loop().time())}")
            logger.info(f"Daily ingestion completed with status: {run.status}")
        except Exception as exc:
            logger.error(f"Daily ingestion failed: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Knowledge Brain service...")
    try:
        await init_db()
        logger.info("Database initialized.")
    except Exception as exc:
        logger.warning(f"Could not initialize DB on startup: {exc}")

    # Start daily background scheduler
    try:
        scheduler.add_job(scheduled_daily_ingestion, "interval", hours=24)
        scheduler.start()
        logger.info("APScheduler daily ingestion job scheduled.")
    except Exception as exc:
        logger.warning(f"Failed to start scheduler: {exc}")

    yield

    # Shutdown
    try:
        scheduler.shutdown()
    except Exception:
        pass
    logger.info("Knowledge Brain service shut down.")


app = FastAPI(
    title="Knowledge Brain API",
    description="Knowledge service for Brilliant Directories solution center supporting Tasks 2 and 3.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health.router, tags=["Health"])
app.include_router(query.router, tags=["RAG Query"])
app.include_router(ingestion.router, tags=["Ingestion"])
app.include_router(escalation.router, tags=["Escalations"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.TASK1_PORT, reload=True)
