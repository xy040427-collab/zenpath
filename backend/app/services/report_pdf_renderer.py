"""
report_pdf_renderer.py — Playwright-based PDF renderer for ZENPATH reports.

Opens the dedicated PDF preview page (/report/pdf-preview/:id) in headless Chromium,
waits for data load, and exports a production-quality A4 PDF.

Design: uses sync Playwright API wrapped in asyncio.to_thread() — cleaner than mixing
async Playwright with FastAPI's event loop and avoids browser lifecycle issues.
"""

import os
import logging
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PwTimeoutError

logger = logging.getLogger(__name__)

# PDF preview page is served by the same FastAPI server (Mode A: single process)
BASE_URL = os.environ.get("ZENPATH_BASE_URL", "http://127.0.0.1:3457")
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "generated" / "reports"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Playwright timeouts (milliseconds)
PAGE_LOAD_TIMEOUT = 60_000    # network idle
READY_TIMEOUT = 60_000        # __ZENPATH_PDF_READY__ signal


def render_pdf(report_id: str) -> dict:
    """Render the PDF preview page to a real PDF file.

    Returns:
        dict with keys:
        - success (bool)
        - file_path (str | None) — absolute path to generated PDF
        - file_name (str | None) — download filename
        - error_message (str | None)

    The PDF preview page MUST set window.__ZENPATH_PDF_READY__ = true
    after all data, fonts, and charts have loaded. The renderer polls
    this flag to avoid capturing a half-rendered page.
    """
    url = f"{BASE_URL}/#/report/pdf-preview/{report_id}"
    output_path = OUTPUT_DIR / f"{report_id}.pdf"
    file_name = f"择境志愿填报分析报告_{report_id}.pdf"

    logger.info(f"Rendering PDF for report {report_id}: {url} -> {output_path}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1240, "height": 1754},
            device_scale_factor=1,
        )

        try:
            # Navigate and wait for network to settle
            page.goto(url, wait_until="networkidle", timeout=PAGE_LOAD_TIMEOUT)

            # Wait for the page's ready signal — data, fonts, charts loaded
            page.wait_for_function(
                "window.__ZENPATH_PDF_READY__ === true",
                timeout=READY_TIMEOUT,
            )

            # Small extra wait for any post-ready layout settling
            page.wait_for_timeout(500)

            # Generate PDF
            # print_background=False to avoid huge PDFs crashing Playwright's JSON transport
            page.pdf(
                path=str(output_path),
                format="A4",
                print_background=False,
                margin={
                    "top": "10mm",
                    "right": "10mm",
                    "bottom": "10mm",
                    "left": "10mm",
                },
            )

            logger.info(f"PDF generated: {output_path} ({output_path.stat().st_size} bytes)")

            return {
                "success": True,
                "file_path": str(output_path),
                "file_name": file_name,
                "error_message": None,
            }

        except PwTimeoutError as e:
            logger.error(f"PDF render timeout for report {report_id}: {e}")
            return {
                "success": False,
                "file_path": None,
                "file_name": None,
                "error_message": f"PDF 生成超时: {str(e)[:200]}",
            }

        except Exception as e:
            logger.exception(f"PDF render failed for report {report_id}")
            return {
                "success": False,
                "file_path": None,
                "file_name": None,
                "error_message": f"PDF 生成失败: {str(e)[:200]}",
            }

        finally:
            browser.close()
