"""Hacker News scraping for Intuned APIs (uses the Intuned Browser SDK)."""

from intuned_browser import go_to_url
from playwright.async_api import Page

from utils.extract import EXTRACT_STORIES_JS, HN_FRONT_PAGE

__all__ = ["scrape_front_page", "EXTRACT_STORIES_JS", "HN_FRONT_PAGE"]


async def scrape_front_page(page: Page, pages: int = 1) -> list[dict]:
    """
    Scrape one or more Hacker News front-page listing pages.

    Each listing page holds ~30 stories. Set `pages` > 1 to follow the "More"
    link and collect additional pages. Returns a flat list of story dicts with:
    id, rank, title, url, site, score, author, comments, comments_url, age,
    created_at.
    """
    pages = max(1, int(pages))
    stories: list[dict] = []

    await go_to_url(page, url=HN_FRONT_PAGE, wait_for_load_using_ai=False)

    for current in range(1, pages + 1):
        page_stories = await page.evaluate(EXTRACT_STORIES_JS)
        stories.extend(page_stories)
        print(f"[hacker-news] page {current}: scraped {len(page_stories)} stories")

        if current >= pages:
            break

        # Follow the "More" link to the next listing page, if present.
        more_link = page.locator("a.morelink")
        if await more_link.count() == 0:
            print("[hacker-news] no 'More' link found, stopping pagination")
            break
        next_href = await more_link.first.get_attribute("href")
        if not next_href:
            break
        await go_to_url(
            page,
            url=f"https://news.ycombinator.com/{next_href}",
            wait_for_load_using_ai=False,
        )

    return stories
