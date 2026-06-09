"""Standalone local runner — no Intuned CLI required.

Scrapes the Hacker News front page with plain Playwright, enriches the top
stories with the LLM (Chinese translate / classify / summarize), and pushes the
digest to Telegram. Reads configuration from a local `.env` file.

Usage (from this folder):

    uv sync
    uv run playwright install chromium     # one-time browser download
    uv run python run_local.py             # scrape -> translate -> send to Telegram
    uv run python run_local.py --no-send   # dry run: print preview only
    uv run python run_local.py --limit 5   # only the top 5 stories
"""

import argparse
import asyncio
import datetime
import os
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))


def load_dotenv(path: Path) -> None:
    """Minimal .env loader (no extra dependency)."""
    if not path.exists():
        print(f"[local] WARNING: {path} not found — copy .env.example to .env and fill it in")
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run the HN→Telegram digest locally")
    parser.add_argument("--limit", type=int, default=10, help="top N stories to push")
    parser.add_argument("--no-send", action="store_true", help="print preview, do not send")
    args = parser.parse_args()

    load_dotenv(HERE / ".env")

    # Imported after .env is loaded; these only use stdlib + httpx (no Intuned runtime).
    from playwright.async_api import async_playwright

    from utils.extract import EXTRACT_STORIES_JS, HN_FRONT_PAGE
    from utils.llm import enrich_stories
    from utils.telegram import build_digest_message, send_message

    # 1. Scrape with plain Playwright.
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print(f"[local] navigating to {HN_FRONT_PAGE}")
        await page.goto(HN_FRONT_PAGE, wait_until="domcontentloaded", timeout=60_000)
        stories = await page.evaluate(EXTRACT_STORIES_JS)
        await browser.close()

    top = stories[: max(1, args.limit)]
    print(f"[local] scraped {len(stories)} stories, taking top {len(top)}")

    # 2. LLM enrichment (Chinese translation + category + summary).
    enriched = await enrich_stories(top)

    # 3. Build the digest message.
    today = datetime.date.today().isoformat()
    header = f"📰 Hacker News 每日精选 · {today}"
    message = build_digest_message(enriched, header)

    print("\n========== Telegram message preview ==========\n")
    print(message)
    print("\n==============================================\n")

    # 4. Send to Telegram.
    if args.no_send:
        print("[local] --no-send: skipped Telegram delivery")
        return
    responses = await send_message(message)
    chat_id = os.environ.get("TELEGRAM_APPROVAL_CHAT_ID")
    print(f"[local] ✅ sent {len(responses)} Telegram chunk(s) to chat {chat_id}")


if __name__ == "__main__":
    asyncio.run(main())
