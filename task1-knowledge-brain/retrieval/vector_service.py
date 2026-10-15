import math
import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.knowledge import Article, Chunk, Screenshot


def compute_deterministic_embedding(text: str, dim: int = settings.EMBEDDING_DIM) -> List[float]:
    """Fast, deterministic semantic projection embedding for reproducible, zero-external-dependency vector search."""
    vec = [0.0] * dim
    words = re.findall(r"\w+", text.lower())
    if not words:
        return vec

    # Project words and bigrams into vector space using stable salted hashes
    for i, word in enumerate(words):
        h = int(hashlib.md5(word.encode()).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
        vec[idx] += sign * (1.0 + 1.0 / (1.0 + math.log(len(word) + 1)))

        if i + 1 < len(words):
            bigram = f"{word}_{words[i+1]}"
            h2 = int(hashlib.md5(bigram.encode()).hexdigest(), 16)
            idx2 = h2 % dim
            sign2 = 1.0 if (h2 >> 8) % 2 == 0 else -1.0
            vec[idx2] += sign2 * 1.5

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 1e-9:
        vec = [x / norm for x in vec]
    return vec


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute dot product of two normalized unit vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    return max(0.0, min(1.0, (dot + 1.0) / 2.0))  # Scale [-1, 1] to [0, 1]


def compute_keyword_score(query: str, text: str, title: str = "") -> float:
    """Lexical keyword score for hybrid search."""
    q_words = set(re.findall(r"\w+", query.lower()))
    if not q_words:
        return 0.0

    target = f"{title} {text}".lower()
    matches = 0
    for w in q_words:
        if len(w) > 2 and w in target:
            # Bonus if in title
            matches += 2.0 if w in title.lower() else 1.0

    max_possible = len(q_words) * 2.0
    return min(1.0, matches / max_possible if max_possible > 0 else 0.0)


class VectorService:
    def __init__(self, embedding_dim: int = settings.EMBEDDING_DIM):
        self.embedding_dim = embedding_dim

    def embed_text(self, text: str) -> List[float]:
        return compute_deterministic_embedding(text, dim=self.embedding_dim)

    async def search(
        self,
        db: AsyncSession,
        query: str,
        top_k: int = settings.RETRIEVAL_TOP_K,
        threshold: float = settings.SIMILARITY_THRESHOLD,
    ) -> List[Dict[str, Any]]:
        """Hybrid search combining vector similarity and keyword matching across active articles."""
        query_vec = self.embed_text(query)

        # Retrieve chunks with active parent articles
        stmt = (
            select(Chunk, Article)
            .join(Article, Chunk.article_id == Article.id)
            .where(Article.is_active == True)
        )
        result = await db.execute(stmt)
        rows = result.all()

        scored_results = []
        for chunk, article in rows:
            chunk_vec = chunk.embedding_json
            if not chunk_vec:
                chunk_vec = self.embed_text(chunk.content)

            sem_score = cosine_similarity(query_vec, chunk_vec)
            kw_score = compute_keyword_score(query, chunk.content, article.title)
            hybrid_score = (0.65 * sem_score) + (0.35 * kw_score)

            if hybrid_score >= threshold:
                # Retrieve associated screenshot URLs if any
                screenshot_stmt = select(Screenshot.url).where(Screenshot.article_id == article.id)
                s_res = await db.execute(screenshot_stmt)
                screenshot_urls = [s[0] for s in s_res.all()]

                scored_results.append({
                    "chunk_id": chunk.id,
                    "article_id": article.id,
                    "article_url": article.url,
                    "article_title": article.title,
                    "heading_path": chunk.heading_path,
                    "content": chunk.content,
                    "score": round(hybrid_score, 4),
                    "semantic_score": round(sem_score, 4),
                    "keyword_score": round(kw_score, 4),
                    "screenshot_urls": screenshot_urls,
                })

        # Sort descending by hybrid score
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]
