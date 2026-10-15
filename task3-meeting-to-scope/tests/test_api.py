import pytest
import pytest_asyncio
import httpx
from app.main import app


@pytest_asyncio.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_task3_api_full_workflow(client):
    # 1. Health check
    health_resp = await client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["service"] == "Task 3: Meeting to Scope"

    # 2. List transcripts
    trx_resp = await client.get("/transcripts")
    assert trx_resp.status_code == 200
    transcripts = trx_resp.json()
    assert len(transcripts) == 3

    # 3. Process Meeting A
    proc_a = await client.post("/transcripts/trx_meeting_a/process")
    assert proc_a.status_code == 200
    prop_a = proc_a.json()
    prop_a_id = prop_a["proposal_id"]
    assert prop_a["status"] == "draft"
    assert prop_a["timeline_weeks"] == 6

    # 4. Attempt to send unapproved proposal -> MUST FAIL with 403 Forbidden!
    send_unauth = await client.post(f"/proposals/{prop_a_id}/send")
    assert send_unauth.status_code == 403
    assert "strictly forbids dispatching" in send_unauth.json()["detail"]

    # 5. Approve proposal
    appr_resp = await client.post(
        f"/proposals/{prop_a_id}/approve",
        json={"reviewer_name": "VP Product", "comments": "Approved for client presentation."},
    )
    assert appr_resp.status_code == 200
    assert appr_resp.json()["status"] == "approved"
    assert appr_resp.json()["approved_by"] == "VP Product"

    # 6. Send approved proposal -> Now succeeds!
    send_auth = await client.post(f"/proposals/{prop_a_id}/send")
    assert send_auth.status_code == 200
    assert send_auth.json()["status"] == "dispatched"

    # 7. Process Meeting C (Follow-up)
    proc_c = await client.post("/transcripts/trx_meeting_c/process")
    assert proc_c.status_code == 200
    prop_c = proc_c.json()
    prop_c_id = prop_c["proposal_id"]
    assert prop_c["version"] == 2
    assert prop_c["timeline_weeks"] == 4

    # 8. Scope Diff between Meeting A baseline and Meeting C follow-up
    diff_resp = await client.post(f"/proposals/diff?baseline_id={prop_a_id}&revised_id={prop_c_id}")
    assert diff_resp.status_code == 200
    diff_data = diff_resp.json()
    assert len(diff_data["added_requirements"]) >= 1
    assert diff_data["timeline_delta_weeks"] == -2
