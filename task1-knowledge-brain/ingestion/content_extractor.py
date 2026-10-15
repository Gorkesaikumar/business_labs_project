import re
import hashlib
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup, Tag


def generate_stable_id(url: str) -> str:
    """Generate stable article ID from URL."""
    # Match Brilliant Directories article ID if in URL (e.g. /articles/123456789)
    match = re.search(r"/articles/(\d+)", url)
    if match:
        return f"art_{match.group(1)}"
    # Fallback to SHA-256 slug
    return f"art_{hashlib.sha256(url.encode()).hexdigest()[:16]}"


def extract_article_content(url: str, html_text: str) -> Dict[str, Any]:
    """Parse HTML and extract clean article text, metadata, headings, tables, and images."""
    soup = BeautifulSoup(html_text, "html.parser")

    # Remove non-content elements
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "form"]):
        tag.decompose()

    # Extract Title
    title = ""
    title_tag = soup.find("h1") or soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)
    if not title:
        title = url.rstrip("/").split("/")[-1].replace("-", " ").title()

    # Category / Breadcrumbs
    category = "General"
    breadcrumb = soup.find("ul", class_=re.compile(r"breadcrumb", re.I)) or soup.find("div", class_=re.compile(r"breadcrumb", re.I))
    if breadcrumb:
        crumbs = [c.get_text(strip=True) for c in breadcrumb.find_all("li") if c.get_text(strip=True)]
        if len(crumbs) > 1:
            category = " > ".join(crumbs[:-1])

    # Canonical URL
    canonical_link = soup.find("link", rel="canonical")
    canonical_url = canonical_link["href"] if canonical_link and "href" in canonical_link.attrs else url

    # Target main article container if available (Freshdesk / BD support uses article or .article-body or #article-body)
    article_container = (
        soup.find("article")
        or soup.find("div", class_=re.compile(r"article-body|article__body|solution-body|content", re.I))
        or soup.find("main")
        or soup.body
        or soup
    )

    # Extract Headings
    headings = []
    for h in article_container.find_all(["h1", "h2", "h3", "h4"]):
        h_text = h.get_text(strip=True)
        if h_text:
            headings.append({
                "level": int(h.name[1]),
                "text": h_text,
                "id": h.get("id", "")
            })

    # Extract Tables
    tables = []
    for t_idx, table in enumerate(article_container.find_all("table")):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        rows = []
        for tr in table.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if cells:
                rows.append(cells)
        if headers or rows:
            tables.append({
                "index": t_idx,
                "headers": headers,
                "rows": rows
            })

    # Extract Images with surrounding text
    images = []
    for img in article_container.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if not src:
            continue
        # Ignore tracking pixels and tiny icons
        if "pixel" in src or "1x1" in src:
            continue
        alt = img.get("alt", "").strip()
        # Find surrounding paragraph or parent context
        parent = img.parent
        surrounding_text = ""
        if parent and parent.name in ["p", "div", "li", "figure"]:
            surrounding_text = parent.get_text(strip=True)
            # Remove alt text from surrounding if duplicated
            if alt and surrounding_text.startswith(alt):
                surrounding_text = surrounding_text[len(alt):].strip()

        images.append({
            "src": src,
            "alt": alt,
            "surrounding_text": surrounding_text[:500] if surrounding_text else ""
        })

    # Clean text
    clean_lines = []
    for elem in article_container.find_all(["p", "h1", "h2", "h3", "h4", "li", "blockquote", "pre", "table"]):
        if elem.name == "table":
            # Convert table to markdown representation for clean reading
            th_cells = [th.get_text(strip=True) for th in elem.find_all("th")]
            if th_cells:
                clean_lines.append("| " + " | ".join(th_cells) + " |")
                clean_lines.append("| " + " | ".join(["---"] * len(th_cells)) + " |")
            for tr in elem.find_all("tr"):
                td_cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if td_cells:
                    clean_lines.append("| " + " | ".join(td_cells) + " |")
            clean_lines.append("")
        else:
            txt = elem.get_text(strip=True)
            if txt:
                if elem.name in ["h1", "h2", "h3", "h4"]:
                    clean_lines.append(f"\n{'#' * int(elem.name[1])} {txt}\n")
                elif elem.name == "li":
                    clean_lines.append(f"- {txt}")
                else:
                    clean_lines.append(txt)

    content = "\n".join(clean_lines).strip()
    if not content:
        content = article_container.get_text(separator="\n", strip=True)

    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    return {
        "id": generate_stable_id(url),
        "url": url,
        "canonical_url": canonical_url,
        "title": title,
        "content": content,
        "html": str(article_container),
        "headings": headings,
        "tables": tables,
        "images": images,
        "category": category,
        "content_hash": content_hash,
    }
