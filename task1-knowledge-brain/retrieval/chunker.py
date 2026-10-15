import re
from typing import List, Dict, Any, Optional
from app.core.config import settings


def split_into_semantic_chunks(
    article_id: str,
    article_url: str,
    title: str,
    content: str,
    headings: List[Dict[str, Any]],
    screenshots: Optional[List[Dict[str, Any]]] = None,
    chunk_size: int = settings.CHUNK_SIZE,
    chunk_overlap: int = settings.CHUNK_OVERLAP,
) -> List[Dict[str, Any]]:
    """Split article into semantically bounded chunks preserving headings, tables, and image context."""
    chunks = []
    paragraphs = re.split(r"\n\s*\n", content)

    current_heading = "Overview"
    current_chunk_text = []
    current_tokens = 0
    chunk_idx = 0

    # Build image context string if available
    img_notes = []
    if screenshots:
        for s in screenshots:
            if s.get("description"):
                img_notes.append(f"[Image Context: {s['description']}]")
    image_context_block = "\n".join(img_notes)

    for p in paragraphs:
        p_clean = p.strip()
        if not p_clean:
            continue

        # Check if paragraph is a heading
        if p_clean.startswith("#"):
            heading_match = re.match(r"^#+\s+(.+)$", p_clean)
            if heading_match:
                # If we have accumulated enough text, flush current chunk
                if current_chunk_text and current_tokens >= chunk_size // 2:
                    full_text = "\n\n".join(current_chunk_text)
                    chunks.append({
                        "id": f"{article_id}_chunk_{chunk_idx}",
                        "article_id": article_id,
                        "article_url": article_url,
                        "article_title": title,
                        "chunk_index": chunk_idx,
                        "heading_path": current_heading,
                        "content": full_text,
                        "token_count": len(full_text.split()),
                    })
                    chunk_idx += 1
                    current_chunk_text = []
                    current_tokens = 0

                current_heading = heading_match.group(1).strip()
                continue

        p_words = len(p_clean.split())

        # If adding this paragraph exceeds chunk size and we already have content, flush
        if current_tokens + p_words > chunk_size and current_chunk_text:
            full_text = "\n\n".join(current_chunk_text)
            chunks.append({
                "id": f"{article_id}_chunk_{chunk_idx}",
                "article_id": article_id,
                "article_url": article_url,
                "article_title": title,
                "chunk_index": chunk_idx,
                "heading_path": current_heading,
                "content": full_text,
                "token_count": len(full_text.split()),
            })
            chunk_idx += 1

            # Keep overlap: last paragraph
            overlap_p = current_chunk_text[-1] if current_chunk_text else ""
            current_chunk_text = [overlap_p] if overlap_p and len(overlap_p.split()) <= chunk_overlap else []
            current_tokens = sum(len(x.split()) for x in current_chunk_text)

        current_chunk_text.append(p_clean)
        current_tokens += p_words

    # Flush remaining text
    if current_chunk_text:
        full_text = "\n\n".join(current_chunk_text)
        # Attach image notes to final or relevant chunk if applicable
        if image_context_block and len(full_text.split()) + len(image_context_block.split()) <= chunk_size * 1.5:
            full_text += f"\n\n{image_context_block}"
        chunks.append({
            "id": f"{article_id}_chunk_{chunk_idx}",
            "article_id": article_id,
            "article_url": article_url,
            "article_title": title,
            "chunk_index": chunk_idx,
            "heading_path": current_heading,
            "content": full_text,
            "token_count": len(full_text.split()),
        })

    return chunks
