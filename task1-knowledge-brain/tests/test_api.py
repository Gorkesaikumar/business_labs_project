import pytest
import pytest_asyncio
import httpx
from app.main import app
from app.db.session import get_db
from app.core.config import settings
from app.models.knowledge import Article, Chunk


@pytest_asyncio.fixture
async def async_client(test_db):
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_api_health_endpoint(async_client):
    resp = await async_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "Task 1: Knowledge Brain"
    assert data["status"] in ("healthy", "degraded")


@pytest.mark.asyncio
async def test_api_query_endpoint(async_client, test_db):
    # Seed article
    art = Article(
        id="art_api_test",
        url="https://support.brilliantdirectories.com/support/solutions/articles/api-test",
        canonical_url="https://support.brilliantdirectories.com/support/solutions/articles/api-test",
        title="Custom CSS in Design Settings",
        content="Administrators can inject custom CSS styles in Design Settings > Custom CSS.",
        headings=[{"level": 1, "text": "Design", "id": "design"}],
        tables=[],
        category="Design",
        content_hash="css_hash",
        version=1,
        is_active=True,
    )
    test_db.add(art)
    test_db.add(Chunk(
        id="art_api_test_chunk_0",
        article_id="art_api_test",
        chunk_index=0,
        heading_path="Design",
        content=art.content,
        token_count=12,
        embedding_json=None,
    ))
    await test_db.commit()

    resp = await async_client.post(
        "/query",
        json={"question": "Where can I add custom CSS in Brilliant Directories?", "threshold": 0.3},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "answered"
    assert len(data["sources"]) >= 1
    assert "Custom CSS" in data["answer"]


@pytest.mark.asyncio
async def test_api_escalation_and_auth(async_client):
    # 1. Create escalation
    create_resp = await async_client.post(
        "/escalations",
        json={"question": "How to set up SSO with Okta?", "reason": "No SSO documentation found."},
    )
    assert create_resp.status_code == 200
    esc_data = create_resp.json()
    esc_id = esc_data["id"]

    # 2. Try to resolve without admin key -> should fail with 401
    resolve_unauth = await async_client.post(
        f"/escalations/{esc_id}/resolve",
        json={"expert_answer": "SSO with Okta requires the Enterprise SAML add-on.", "approved_by": "Security Officer"},
    )
    assert resolve_unauth.status_code == 401

    # 3. Resolve with valid admin key -> 200
    resolve_auth = await async_client.post(
        f"/escalations/{esc_id}/resolve",
        headers={"X-API-Key": settings.TASK1_API_KEY},
        json={"expert_answer": "SSO with Okta requires the Enterprise SAML add-on.", "approved_by": "Security Officer"},
    )
    assert resolve_auth.status_code == 200
    assert resolve_auth.json()["status"] == "resolved"
