import asyncio
import hashlib
import logging
import random
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set, Tuple
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.config import settings
from app.models.knowledge import Article, IngestionRun, IngestionManifest
from .content_extractor import extract_article_content

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SitemapCrawler:
    def __init__(
        self,
        sitemap_url: str = settings.SITEMAP_URL,
        max_pages: int = settings.CRAWL_MAX_PAGES,
        concurrency: int = settings.CRAWL_CONCURRENCY,
        delay_seconds: float = settings.CRAWL_DELAY_SECONDS,
        user_agent: str = settings.USER_AGENT,
    ):
        self.sitemap_url = sitemap_url
        self.max_pages = max_pages
        self.concurrency = concurrency
        self.delay_seconds = delay_seconds
        self.user_agent = user_agent
        self.headers = {"User-Agent": self.user_agent, "Accept": "application/xml,text/html,*/*"}

    async def fetch_sitemap_urls(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        """Fetch and parse sitemap XML, supporting sub-sitemaps and deduplication."""
        logger.info(f"Fetching sitemap from: {self.sitemap_url}")
        resp = await client.get(self.sitemap_url, headers=self.headers, timeout=settings.CRAWL_TIMEOUT_SECONDS)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        # Handle default namespace if present
        ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        # Check for sitemap index (<sitemapindex>)
        sub_sitemaps = root.findall(".//ns:sitemap/ns:loc", ns)
        if sub_sitemaps:
            urls = []
            for sm in sub_sitemaps:
                sub_url = sm.text.strip() if sm.text else ""
                if sub_url:
                    sub_resp = await client.get(sub_url, headers=self.headers, timeout=settings.CRAWL_TIMEOUT_SECONDS)
                    if sub_resp.status_code == 200:
                        sub_root = ET.fromstring(sub_resp.content)
                        for url_node in sub_root.findall(".//ns:url", ns):
                            loc = url_node.find("ns:loc", ns)
                            lastmod = url_node.find("ns:lastmod", ns)
                            if loc is not None and loc.text:
                                urls.append({
                                    "loc": loc.text.strip(),
                                    "lastmod": lastmod.text.strip() if lastmod is not None and lastmod.text else None
                                })
            return urls

        # Direct <urlset>
        urls = []
        for url_node in root.findall(".//ns:url", ns):
            loc = url_node.find("ns:loc", ns)
            lastmod = url_node.find("ns:lastmod", ns)
            if loc is not None and loc.text:
                urls.append({
                    "loc": loc.text.strip(),
                    "lastmod": lastmod.text.strip() if lastmod is not None and lastmod.text else None
                })
        return urls

    async def fetch_page_with_retry(
        self,
        client: httpx.AsyncClient,
        url: str,
        max_retries: int = 3,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
    ) -> Tuple[Optional[httpx.Response], Optional[str]]:
        """Polite page fetch with exponential backoff and jitter."""
        req_headers = dict(self.headers)
        if etag:
            req_headers["If-None-Match"] = etag
        if last_modified:
            req_headers["If-Modified-Since"] = last_modified

        for attempt in range(1, max_retries + 1):
            try:
                # Polite concurrency delay
                await asyncio.sleep(self.delay_seconds + random.uniform(0.05, 0.2))
                response = await client.get(
                    url,
                    headers=req_headers,
                    timeout=settings.CRAWL_TIMEOUT_SECONDS,
                    follow_redirects=True,
                )
                if response.status_code == 429 or response.status_code >= 500:
                    wait_time = (2 ** attempt) + random.uniform(0.1, 0.5)
                    logger.warning(f"HTTP {response.status_code} on {url}. Retrying in {wait_time:.1f}s (attempt {attempt}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                return response, None
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                wait_time = (2 ** attempt) + random.uniform(0.1, 0.5)
                logger.warning(f"Network error on {url}: {exc}. Retrying in {wait_time:.1f}s (attempt {attempt}/{max_retries})")
                await asyncio.sleep(wait_time)
                if attempt == max_retries:
                    return None, str(exc)
        return None, "Max retries exceeded"

    async def run_crawl(
        self,
        db: AsyncSession,
        run_id: str,
        force_resync: bool = False,
    ) -> IngestionRun:
        """Execute resumable crawl and update database."""
        ingestion_run = IngestionRun(
            id=run_id,
            started_at=utcnow(),
            status="running",
        )
        db.add(ingestion_run)
        await db.commit()

        total_discovered = 0
        added_count = 0
        updated_count = 0
        unchanged_count = 0
        error_count = 0

        async with httpx.AsyncClient(verify=True) as client:
            try:
                raw_urls = await self.fetch_sitemap_urls(client)
                # Prioritize articles over category lists
                article_entries = [u for u in raw_urls if "/solutions/articles/" in u["loc"]]
                if not article_entries:
                    article_entries = raw_urls

                # Enforce max_pages limit
                target_entries = article_entries[: self.max_pages]
                total_discovered = len(target_entries)
                logger.info(f"Targeting {total_discovered} pages for crawl.")

                sem = asyncio.Semaphore(self.concurrency)

                async def process_entry(entry: Dict[str, Any]):
                    nonlocal added_count, updated_count, unchanged_count, error_count
                    url = entry["loc"]
                    sitemap_lastmod = entry.get("lastmod")

                    async with sem:
                        # Check manifest for resumability
                        stmt = select(IngestionManifest).where(IngestionManifest.url == url)
                        result = await db.execute(stmt)
                        manifest_entry = result.scalar_one_or_none()

                        prev_etag = manifest_entry.etag if manifest_entry else None
                        prev_lastmod = manifest_entry.last_modified if manifest_entry else None

                        resp, err = await self.fetch_page_with_retry(
                            client,
                            url,
                            etag=None if force_resync else prev_etag,
                            last_modified=None if force_resync else prev_lastmod,
                        )

                        if err or resp is None:
                            error_count += 1
                            if manifest_entry:
                                manifest_entry.attempts += 1
                                manifest_entry.error_details = err
                                manifest_entry.status = "failed"
                            else:
                                db.add(IngestionManifest(
                                    url=url,
                                    status="failed",
                                    attempts=1,
                                    error_details=err,
                                    last_crawled_at=utcnow()
                                ))
                            await db.commit()
                            return

                        if resp.status_code == 304:
                            unchanged_count += 1
                            if manifest_entry:
                                manifest_entry.last_crawled_at = utcnow()
                                manifest_entry.status = "success"
                            await db.commit()
                            return

                        if resp.status_code != 200:
                            error_count += 1
                            if manifest_entry:
                                manifest_entry.attempts += 1
                                manifest_entry.error_details = f"HTTP {resp.status_code}"
                                manifest_entry.status = "failed"
                            else:
                                db.add(IngestionManifest(
                                    url=url,
                                    status="failed",
                                    attempts=1,
                                    error_details=f"HTTP {resp.status_code}",
                                    last_crawled_at=utcnow()
                                ))
                            await db.commit()
                            return

                        # Content extraction
                        extracted = extract_article_content(url, resp.text)
                        content_hash = extracted["content_hash"]
                        article_id = extracted["id"]

                        # Check if article exists and whether hash changed
                        stmt_art = select(Article).where(Article.url == url)
                        res_art = await db.execute(stmt_art)
                        existing_article = res_art.scalar_one_or_none()

                        new_etag = resp.headers.get("etag")
                        new_lastmod = resp.headers.get("last-modified") or sitemap_lastmod

                        if existing_article:
                            if existing_article.content_hash == content_hash and not force_resync:
                                unchanged_count += 1
                                existing_article.is_active = True
                            else:
                                updated_count += 1
                                existing_article.title = extracted["title"]
                                existing_article.content = extracted["content"]
                                existing_article.html = extracted["html"]
                                existing_article.headings = extracted["headings"]
                                existing_article.tables = extracted["tables"]
                                existing_article.category = extracted["category"]
                                existing_article.content_hash = content_hash
                                existing_article.version += 1
                                existing_article.is_active = True
                                existing_article.updated_at = utcnow()
                        else:
                            added_count += 1
                            new_article = Article(
                                id=article_id,
                                url=url,
                                canonical_url=extracted.get("canonical_url", url),
                                title=extracted["title"],
                                content=extracted["content"],
                                html=extracted["html"],
                                headings=extracted["headings"],
                                tables=extracted["tables"],
                                category=extracted["category"],
                                content_hash=content_hash,
                                version=1,
                                is_active=True,
                                created_at=utcnow(),
                                updated_at=utcnow(),
                            )
                            db.add(new_article)

                        # Update manifest
                        if manifest_entry:
                            manifest_entry.article_id = article_id
                            manifest_entry.content_hash = content_hash
                            manifest_entry.etag = new_etag
                            manifest_entry.last_modified = new_lastmod
                            manifest_entry.status = "success"
                            manifest_entry.error_details = None
                            manifest_entry.last_crawled_at = utcnow()
                        else:
                            db.add(IngestionManifest(
                                url=url,
                                article_id=article_id,
                                content_hash=content_hash,
                                etag=new_etag,
                                last_modified=new_lastmod,
                                status="success",
                                attempts=1,
                                error_details=None,
                                last_crawled_at=utcnow()
                            ))
                        await db.commit()

                for entry in target_entries:
                    await process_entry(entry)

                ingestion_run.status = "completed"
                ingestion_run.completed_at = utcnow()
                ingestion_run.total_discovered = total_discovered
                ingestion_run.added_count = added_count
                ingestion_run.updated_count = updated_count
                ingestion_run.unchanged_count = unchanged_count
                ingestion_run.error_count = error_count
                ingestion_run.summary = {
                    "pages_crawled": total_discovered,
                    "added": added_count,
                    "updated": updated_count,
                    "unchanged": unchanged_count,
                    "errors": error_count,
                }
                await db.commit()
                return ingestion_run

            except Exception as exc:
                logger.exception("Ingestion run failed abruptly")
                ingestion_run.status = "failed"
                ingestion_run.completed_at = utcnow()
                ingestion_run.summary = {"error": str(exc)}
                await db.commit()
                return ingestion_run
