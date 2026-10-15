import pytest
import httpx
from ingestion.sitemap_crawler import SitemapCrawler
from app.models.knowledge import IngestionManifest, Article


SAMPLE_SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://support.brilliantdirectories.com/support/solutions/articles/1001</loc>
    <lastmod>2026-10-12T00:00:00+00:00</lastmod>
  </url>
  <url>
    <loc>https://support.brilliantdirectories.com/support/solutions/articles/1002</loc>
    <lastmod>2026-10-12T00:00:00+00:00</lastmod>
  </url>
</urlset>
"""

SAMPLE_ARTICLE_HTML = """<!DOCTYPE html>
<html>
<body>
  <h1>Article 1001 Title</h1>
  <p>Article 1001 content explaining directory configuration steps.</p>
</body>
</html>
"""


@pytest.mark.asyncio
async def test_crawler_fetch_sitemap_urls(monkeypatch):
    crawler = SitemapCrawler(sitemap_url="https://test/sitemap.xml", max_pages=2)

    class MockResponse:
        content = SAMPLE_SITEMAP_XML.encode("utf-8")
        status_code = 200
        def raise_for_status(self):
            pass

    async def mock_get(self, url, *args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    async with httpx.AsyncClient() as client:
        urls = await crawler.fetch_sitemap_urls(client)
        assert len(urls) == 2
        assert urls[0]["loc"] == "https://support.brilliantdirectories.com/support/solutions/articles/1001"
        assert urls[1]["loc"] == "https://support.brilliantdirectories.com/support/solutions/articles/1002"


@pytest.mark.asyncio
async def test_crawler_run_crawl(monkeypatch, test_db):
    crawler = SitemapCrawler(sitemap_url="https://test/sitemap.xml", max_pages=2, delay_seconds=0.01)

    class MockSitemapResponse:
        content = SAMPLE_SITEMAP_XML.encode("utf-8")
        status_code = 200
        def raise_for_status(self):
            pass

    class MockArticleResponse:
        status_code = 200
        text = SAMPLE_ARTICLE_HTML
        headers = {"etag": "etag_1001", "last-modified": "2026-10-12T00:00:00+00:00"}
        def raise_for_status(self):
            pass

    async def mock_get(self, url, *args, **kwargs):
        if "sitemap.xml" in url:
            return MockSitemapResponse()
        return MockArticleResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    run = await crawler.run_crawl(db=test_db, run_id="run_test_crawl_1", force_resync=True)

    assert run.status == "completed"
    assert run.added_count == 2
    assert run.error_count == 0

    # Repeat crawl without force_resync -> should report unchanged
    run2 = await crawler.run_crawl(db=test_db, run_id="run_test_crawl_2", force_resync=False)
    assert run2.status == "completed"
    assert run2.unchanged_count == 2
