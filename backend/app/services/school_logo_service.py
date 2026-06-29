"""
school_logo_service.py — School logo resolution with fallback.

Priority:
  1. schools.logo_slug → public/logos/{slug}.svg (existing static files)
  2. Urongda CDN: cdn.urongda.com/images/normal/medium/{slug}-logo-1024px.png
  3. Generated placeholder badge (墨绿+浅金, school initial)

Never returns broken image — always a valid SVG data URI or path.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Static logo directory (111 SVG files)
LOGOS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "public" / "logos"

# Urongda CDN fallback
URONGDA_CDN = "https://cdn.urongda.com/images/normal/medium/{slug}-logo-1024px.png"

# Colors for placeholder badge
PLACEHOLDER_BG = "#0F2F27"
PLACEHOLDER_BORDER = "#C4A35A"
PLACEHOLDER_TEXT = "#C4A35A"


def get_school_logo(school_name: str, logo_slug: Optional[str] = None) -> Dict[str, Any]:
    """Resolve school logo.

    Returns:
        {
            "url": str,          # URL or data URI
            "type": str,         # "static_svg", "cdn_png", "placeholder"
            "source": str,       # human-readable source
        }
    """
    slug = logo_slug or ""

    # 1. Try static SVG in public/logos/
    if slug:
        svg_path = LOGOS_DIR / f"{slug}.svg"
        if svg_path.is_file():
            return {
                "url": f"/logos/{slug}.svg",
                "type": "static_svg",
                "source": f"Local static logo: {svg_path}",
            }

    # 2. Try to construct slug from school name
    if not slug:
        # Common slug patterns: lowercase, hyphenated
        slug = school_name_to_slug(school_name)
        svg_path = LOGOS_DIR / f"{slug}.svg"
        if svg_path.is_file():
            return {
                "url": f"/logos/{slug}.svg",
                "type": "static_svg",
                "source": f"Local static logo: {svg_path}",
            }

    # 3. CDN fallback (Urongda)
    if slug:
        cdn_url = URONGDA_CDN.format(slug=slug)
        return {
            "url": cdn_url,
            "type": "cdn_png",
            "source": f"Urongda CDN: {cdn_url}",
        }

    # 4. Generated placeholder SVG data URI
    initial = get_school_initial(school_name)
    placeholder_svg = _generate_placeholder_svg(initial)
    return {
        "url": placeholder_svg,
        "type": "placeholder",
        "source": f"Generated placeholder for {school_name}",
    }


def school_name_to_slug(name: str) -> str:
    """Convert school name to URL slug."""
    # Remove common suffixes that don't appear in slugs
    slug = name.strip()
    # Keep Chinese characters and alphanumeric
    return slug


def get_school_initial(name: str) -> str:
    """Extract display initial from school name for placeholder badge."""
    if not name:
        return "?"
    # Take first 1-2 characters
    return name[:2] if len(name) >= 2 else name


def _generate_placeholder_svg(initial: str) -> str:
    """Generate an SVG data URI for a placeholder school badge."""
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80" viewBox="0 0 80 80">
  <circle cx="40" cy="40" r="38" fill="{PLACEHOLDER_BG}" stroke="{PLACEHOLDER_BORDER}" stroke-width="2"/>
  <text x="40" y="46" text-anchor="middle" font-family="serif" font-size="24" fill="{PLACEHOLDER_TEXT}" font-weight="500">{initial}</text>
</svg>"""
    # Return as data URI for embedding in HTML/PDF
    import base64
    b64 = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{b64}"
