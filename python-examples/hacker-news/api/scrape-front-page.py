from typing import TypedDict

from playwright.async_api import Page
from utils.hn import scrape_front_page


class Params(TypedDict, total=False):
    pages: int  # Number of front-page listings to scrape (30 stories each). Default 1.


async def automation(page: Page, params: Params | None = None, **_kwargs):
    """
    Scrape the Hacker News front page.

    For each story it extracts: rank, title, link, score, author, comments count,
    comments URL, posting age and the absolute timestamp.

    Set `pages` > 1 to follow the "More" link and scrape additional listing pages
    (each page holds ~30 stories). The combined result is printed and returned.

    Example params:
    {
        "pages": 1
    }
    """
    params = params or {}
    pages = max(1, int(params.get("pages", 1)))

    stories = await scrape_front_page(page, pages=pages)

    result = {
        "source": "https://news.ycombinator.com/",
        "pages_scraped": pages,
        "count": len(stories),
        "stories": stories,
    }

    # Print the results directly so they show up in the run output.
    print(f"\n[hacker-news] Hacker News front page — {len(stories)} stories\n")
    for story in stories:
        rank = story.get("rank")
        title = story.get("title")
        score = story.get("score")
        author = story.get("author")
        comments = story.get("comments")
        url = story.get("url")
        print(
            f"  {str(rank).rjust(3)}. {title}\n"
            f"       {score if score is not None else 0} points"
            f" | by {author or 'n/a'}"
            f" | {comments if comments is not None else 0} comments\n"
            f"       {url}"
        )

    return result
