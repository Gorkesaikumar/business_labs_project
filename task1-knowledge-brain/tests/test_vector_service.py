import pytest
from retrieval.vector_service import (
    compute_deterministic_embedding,
    cosine_similarity,
    compute_keyword_score,
    VectorService,
)
from app.models.knowledge import Article, Chunk


def test_compute_deterministic_embedding():
    text1 = "How do I configure Stripe payment gateway in Brilliant Directories?"
    text2 = "How do I configure Stripe payment gateway in Brilliant Directories?"
    text3 = "Unrelated weather forecast for London tomorrow morning."

    vec1 = compute_deterministic_embedding(text1)
    vec2 = compute_deterministic_embedding(text2)
    vec3 = compute_deterministic_embedding(text3)

    assert len(vec1) == 384
    # Identical texts must produce identical embeddings
    assert vec1 == vec2

    # Semantic similarity between identical vectors should be 1.0
    sim_identical = cosine_similarity(vec1, vec2)
    assert pytest.approx(sim_identical, 0.001) == 1.0

    # Semantic similarity between unrelated texts should be substantially lower
    sim_unrelated = cosine_similarity(vec1, vec3)
    assert sim_unrelated < 0.8


def test_keyword_score():
    query = "Stripe payment settings"
    matching_text = "To configure Stripe payment, navigate to Settings > Payment Settings."
    non_matching_text = "Users can post blogs and events on the community board."

    score_match = compute_keyword_score(query, matching_text, "Payment Configuration")
    score_nomatch = compute_keyword_score(query, non_matching_text, "Community Board")

    assert score_match > 0.6
    assert score_nomatch == 0.0


@pytest.mark.asyncio
async def test_vector_service_search(test_db):
    service = VectorService()

    # Seed article and chunks
    article = Article(
        id="art_100",
        url="https://support.brilliantdirectories.com/support/solutions/articles/100",
        canonical_url="https://support.brilliantdirectories.com/support/solutions/articles/100",
        title="Connecting Stripe Payment Gateway",
        content="Navigate to Payment Settings and input your Stripe API credentials.",
        headings=[{"level": 1, "text": "Stripe Setup", "id": "stripe"}],
        tables=[],
        category="Finance",
        content_hash="abc100",
        version=1,
        is_active=True,
    )
    test_db.add(article)

    chunk_emb = service.embed_text(article.content)
    chunk = Chunk(
        id="art_100_chunk_0",
        article_id="art_100",
        chunk_index=0,
        heading_path="Stripe Setup",
        content=article.content,
        token_count=10,
        embedding_json=chunk_emb,
    )
    test_db.add(chunk)
    await test_db.commit()

    results = await service.search(test_db, query="How do I connect Stripe?", top_k=3, threshold=0.4)
    assert len(results) >= 1
    assert results[0]["article_id"] == "art_100"
    assert results[0]["score"] >= 0.4
