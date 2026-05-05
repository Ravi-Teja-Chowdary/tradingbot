"""
EUR/USD VisionPulse AI - Visual Perception Layer
Captures high-resolution screenshots of the TradingView EUR/USD chart
using Playwright (headless browser) every 30 minutes.
"""

import os
import asyncio
from datetime import datetime
from pathlib import Path

SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)


async def capture_chart_screenshot() -> str:
    """
    Navigate to TradingView EUR/USD chart and capture a screenshot.
    Returns the file path of the saved screenshot.
    """
    from playwright.async_api import async_playwright

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filepath = str(SCREENSHOTS_DIR / f"eurusd_{timestamp}.png")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=2,
        )
        page = await context.new_page()

        # TradingView advanced chart widget for EUR/USD (public, no login needed)
        chart_url = (
            "https://www.tradingview.com/chart/?symbol=FX_IDC%3AEURUSD&interval=30"
        )

        try:
            await page.goto(chart_url, wait_until="networkidle", timeout=60000)

            # Wait for chart canvas to render
            await page.wait_for_timeout(8000)

            # Dismiss any popups / cookie banners
            for selector in [
                "button:has-text('Accept')",
                "button:has-text('Got it')",
                "button:has-text('OK')",
                "[class*='close']",
            ]:
                try:
                    el = page.locator(selector).first
                    if await el.is_visible(timeout=2000):
                        await el.click()
                        await page.wait_for_timeout(500)
                except Exception:
                    pass

            await page.wait_for_timeout(3000)

            # Take a full-page screenshot
            await page.screenshot(path=filepath, full_page=False, type="png")
            print(f"[VisualPerception] Screenshot saved: {filepath}")

        except Exception as e:
            print(f"[VisualPerception] Error capturing screenshot: {e}")
            # Create a fallback placeholder
            _create_placeholder_screenshot(filepath)

        finally:
            await browser.close()

    return filepath


def _create_placeholder_screenshot(filepath: str):
    """Create a placeholder image if screenshot capture fails."""
    try:
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGB", (1920, 1080), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        draw.text(
            (700, 500),
            "EUR/USD Chart - Screenshot Unavailable",
            fill=(200, 200, 200),
        )
        draw.text(
            (700, 540),
            f"Timestamp: {datetime.utcnow().isoformat()}",
            fill=(150, 150, 150),
        )
        img.save(filepath)
        print(f"[VisualPerception] Placeholder screenshot created: {filepath}")
    except ImportError:
        print("[VisualPerception] Pillow not installed, skipping placeholder.")


def get_latest_screenshot() -> str | None:
    """Return the path to the most recent screenshot, or None."""
    screenshots = sorted(SCREENSHOTS_DIR.glob("eurusd_*.png"))
    if screenshots:
        return str(screenshots[-1])
    return None


def cleanup_old_screenshots(keep_last: int = 48):
    """Remove old screenshots, keeping only the most recent ones."""
    screenshots = sorted(SCREENSHOTS_DIR.glob("eurusd_*.png"))
    if len(screenshots) > keep_last:
        for old in screenshots[:-keep_last]:
            old.unlink()
            print(f"[VisualPerception] Deleted old screenshot: {old}")


def capture_chart_sync() -> str:
    """Synchronous wrapper around the async screenshot capture."""
    return asyncio.run(capture_chart_screenshot())


if __name__ == "__main__":
    path = capture_chart_sync()
    print(f"Captured: {path}")
