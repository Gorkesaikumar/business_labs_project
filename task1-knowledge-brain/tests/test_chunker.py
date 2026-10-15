import pytest
from retrieval.chunker import split_into_semantic_chunks

def test_split_into_semantic_chunks():
    article_id = "art_test_101"
    url = "https://support.brilliantdirectories.com/support/solutions/articles/101"
    title = "Member Sign Up Workflows"
    content = """# Overview
This article describes the member signup process on Brilliant Directories.
Members can register using email or social logins.

# Configuring Form Fields
Navigate to My Members > Member Forms to customize registration fields.
You can make specific fields required or optional.

# Managing Membership Plans
Under Finance > Membership Plans, administrators can set pricing and billing intervals."""

    headings = [
        {"level": 1, "text": "Overview", "id": "overview"},
        {"level": 1, "text": "Configuring Form Fields", "id": "fields"},
        {"level": 1, "text": "Managing Membership Plans", "id": "plans"},
    ]

    chunks = split_into_semantic_chunks(
        article_id=article_id,
        article_url=url,
        title=title,
        content=content,
        headings=headings,
        chunk_size=50,
        chunk_overlap=10,
    )

    assert len(chunks) >= 2
    for chunk in chunks:
        assert chunk["article_id"] == article_id
        assert chunk["article_title"] == title
        assert chunk["token_count"] > 0
        assert chunk["id"].startswith("art_test_101_chunk_")


def test_chunker_with_screenshot_context():
    article_id = "art_test_102"
    url = "https://support.brilliantdirectories.com/support/solutions/articles/102"
    title = "Search Settings"
    content = "Search settings can be configured in General Settings."
    screenshots = [{"description": "Admin dashboard showing Search Settings toggle."}]

    chunks = split_into_semantic_chunks(
        article_id=article_id,
        article_url=url,
        title=title,
        content=content,
        headings=[],
        screenshots=screenshots,
    )

    assert len(chunks) == 1
    assert "Image Context: Admin dashboard showing Search Settings toggle." in chunks[0]["content"]
