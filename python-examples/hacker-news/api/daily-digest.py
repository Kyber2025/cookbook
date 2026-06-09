import datetime
from typing import TypedDict

from playwright.async_api import Page
from utils.hn import scrape_front_page
from utils.llm import enrich_stories
from utils.telegram import build_digest_message, send_message


class Params(TypedDict, total=False):
    pages: int  # Front-page listings to scrape (30 stories each). Default 1.
    limit: int  # How many top stories to translate + push. Default 10.
    send: bool  # Actually send to Telegram. Default True (set False for a dry run).


async def automation(page: Page, params: Params | None = None, **_kwargs):
    """
    Daily Hacker News digest → Telegram.

    Pipeline:
      1. Scrape the HN front page.
      2. Use an LLM (gpt-5.4) to translate each title to Chinese, classify it,
         and write a one-line Chinese summary.
      3. Format a grouped digest and push it to Telegram.

    Designed to run on a daily schedule (see README — every morning at 09:00).

    Example params:
    {
        "pages": 1,
        "limit": 10,
        "send": true
    }
    """
    params = params or {}
    pages = max(1, int(params.get("pages", 1)))
    limit = max(1, int(params.get("limit", 10)))
    send = params.get("send", True)

    # 1. Scrape
    stories = await scrape_front_page(page, pages=pages)
    top = stories[:limit]
    print(f"[digest] scraped {len(stories)} stories, taking top {len(top)}")

    # 2. Enrich with the LLM (Chinese translation + category + summary)
    enriched = await enrich_stories(top)

    # 3. Build the message
    today = datetime.date.today().isoformat()
    header = f"📰 Hacker News 每日精选 · {today}"
    message = build_digest_message(enriched, header)

    print("\n========== Telegram message preview ==========\n")
    print(message)
    print("\n==============================================\n")

    # 4. Send to Telegram
    sent = False
    telegram_responses = []
    if send:
        telegram_responses = await send_message(message)
        sent = True
        print(f"[digest] sent {len(telegram_responses)} Telegram message chunk(s)")
    else:
        print("[digest] send=false — skipped Telegram delivery (dry run)")

    return {
        "date": today,
        "count": len(enriched),
        "sent": sent,
        "telegram_chunks": len(telegram_responses),
        "stories": enriched,
    }
