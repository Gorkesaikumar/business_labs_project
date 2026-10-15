import json
import pytest
from pathlib import Path
from agents.transcript_analyst import TranscriptAnalystAgent

DATASETS_DIR = Path(__file__).parent.parent.parent / "datasets" / "transcripts"


def test_analyze_meeting_a():
    agent = TranscriptAnalystAgent()
    with open(DATASETS_DIR / "meeting_a.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    res = agent.analyze_transcript(data)

    assert res["project_id"] == "proj_directory_search"
    assert res["timeline_weeks"] == 6
    assert len(res["requirements"]) >= 3
    assert len(res["exclusions"]) >= 1
    assert "No native iOS or Android App Store mobile applications" in res["exclusions"][0]

    # Verify requirements have speaker attribution and source passage
    for req in res["requirements"]:
        assert req["speaker"] in ("Tom Chen", "Sarah Miller")
        assert len(req["source_passage"]) > 10
        assert len(req["acceptance_criteria"]) >= 1


def test_analyze_meeting_b():
    agent = TranscriptAnalystAgent()
    with open(DATASETS_DIR / "meeting_b.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    res = agent.analyze_transcript(data)
    assert res["project_id"] == "proj_ecommerce_checkout"
    assert res["timeline_weeks"] == 5
    assert len(res["requirements"]) >= 3
    assert any("Stripe Elements" in r["title"] for r in res["requirements"])


def test_analyze_meeting_c_followup():
    agent = TranscriptAnalystAgent()
    with open(DATASETS_DIR / "meeting_c.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    res = agent.analyze_transcript(data)
    assert res["timeline_weeks"] == 4  # Accelerated deadline
    assert any("AI Conversational" in r["title"] for r in res["requirements"])
    assert any(r["change_type"] == "added" for r in res["requirements"])
