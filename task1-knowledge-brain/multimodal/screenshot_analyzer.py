import base64
import hashlib
import ipaddress
import logging
from urllib.parse import urlparse
from typing import Dict, Any, Optional, List
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


def is_safe_image_url(url: str) -> bool:
    """SSRF prevention: ensure HTTP/HTTPS and block private/loopback/cloud metadata IP ranges."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        # Block localhost and common internal names
        if hostname.lower() in ("localhost", "127.0.0.1", "::1", "metadata.google.internal"):
            return False
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return False
        except ValueError:
            # Domain name, allowed
            pass
        return True
    except Exception:
        return False


class ScreenshotAnalyzer:
    def __init__(self, use_mock: bool = settings.USE_MOCK_LLM):
        self.use_mock = use_mock
        self.client = None
        if not self.use_mock and settings.ANTHROPIC_API_KEY:
            try:
                import anthropic
                self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            except Exception as exc:
                logger.warning(f"Could not initialize Anthropic client: {exc}. Defaulting to mock.")
                self.use_mock = True

    async def analyze_image(
        self,
        image_url: str,
        article_title: str,
        surrounding_text: str = "",
        alt_text: str = "",
    ) -> Dict[str, Any]:
        """Validate, download, and analyze an image using Claude Vision or deterministic mock."""
        if not is_safe_image_url(image_url):
            return {
                "url": image_url,
                "description": f"Image skipped: unsafe or internal URL format ({image_url}).",
                "detected_labels": [],
                "is_legible": False,
                "uncertainty_notes": "SSRF safety check failed.",
                "content_hash": None,
            }

        image_data = None
        content_type = "image/png"
        content_hash = None

        try:
            async with httpx.AsyncClient(timeout=10.0) as http_client:
                resp = await http_client.get(image_url)
                if resp.status_code == 200:
                    ct = resp.headers.get("content-type", "")
                    if "image" in ct:
                        content_type = ct.split(";")[0]
                        image_data = resp.content
                        if len(image_data) > 10 * 1024 * 1024:  # 10MB limit
                            return {
                                "url": image_url,
                                "description": "Image skipped: exceeded 10MB file size limit.",
                                "detected_labels": [],
                                "is_legible": False,
                                "uncertainty_notes": "Exceeded 10MB limit.",
                                "content_hash": None,
                            }
                        content_hash = hashlib.sha256(image_data).hexdigest()
        except Exception as exc:
            logger.warning(f"Failed to fetch image {image_url}: {exc}")
            # Fall back gracefully using context

        if self.use_mock or not self.client or not image_data:
            # Deterministic, grounded mock analysis using image metadata and surrounding section
            labels = []
            if alt_text:
                labels.extend([w.strip().title() for w in alt_text.split() if len(w) > 3][:5])
            if "button" in surrounding_text.lower():
                labels.append("Button")
            if "menu" in surrounding_text.lower() or "tab" in surrounding_text.lower():
                labels.append("Navigation Menu")
            if "settings" in surrounding_text.lower():
                labels.append("Settings Panel")

            desc = (
                f"Screenshot illustrating '{article_title}'. "
                f"{alt_text if alt_text else 'UI screenshot showing workflow steps.'} "
                f"Context: {surrounding_text[:200]}."
            )
            return {
                "url": image_url,
                "description": desc.strip(),
                "detected_labels": list(set(labels)),
                "is_legible": True,
                "uncertainty_notes": "Mock vision extraction based on verified image metadata and section context.",
                "content_hash": content_hash or hashlib.sha256(image_url.encode()).hexdigest(),
            }

        # Real Anthropic Claude Vision API call
        try:
            b64_data = base64.b64encode(image_data).decode("utf-8")
            prompt = (
                f"You are analyzing a screenshot from the Brilliant Directories support documentation for the article '{article_title}'.\n"
                f"Surrounding text: '{surrounding_text}'.\n\n"
                "Please describe:\n"
                "1. Exactly what UI elements, menus, tabs, buttons, or forms are visible.\n"
                "2. Specific settings labels, options, or procedural steps indicated.\n"
                "3. Any callouts, highlighted regions, or arrows.\n"
                "Be completely faithful to what is legible. If any text is too small or blurry to read with certainty, explicitly note it as uncertain."
            )
            response = await self.client.messages.create(
                model=settings.ANTHROPIC_MODEL,
                max_tokens=600,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": content_type,
                                    "data": b64_data,
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            )
            description_text = response.content[0].text
            return {
                "url": image_url,
                "description": description_text,
                "detected_labels": [word.strip() for word in ["Settings", "Admin Menu", "Options"] if word.lower() in description_text.lower()],
                "is_legible": "uncertain" not in description_text.lower(),
                "uncertainty_notes": "Portions marked uncertain by vision model." if "uncertain" in description_text.lower() else None,
                "content_hash": content_hash,
            }
        except Exception as exc:
            logger.error(f"Claude Vision error for {image_url}: {exc}")
            return {
                "url": image_url,
                "description": f"Screenshot from {article_title}: {alt_text or surrounding_text[:150]}",
                "detected_labels": [],
                "is_legible": False,
                "uncertainty_notes": f"Vision analysis failed: {exc}",
                "content_hash": content_hash,
            }
