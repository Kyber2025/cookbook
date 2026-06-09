"""Shared Hacker News scraping helpers."""

from playwright.async_api import Page

from intuned_browser import go_to_url

HN_FRONT_PAGE = "https://news.ycombinator.com/"

# A single, fast DOM pass that reads every story row (`tr.athing`) on the current
# page together with its sibling subtext row. Running this in the browser avoids
# dozens of Playwright round-trips and keeps extraction resilient to missing
# fields (job posts have no score/author/comments).
EXTRACT_STORIES_JS = r"""
() => {
  const toInt = (text) => {
    if (!text) return null;
    const m = text.replace(/,/g, '').match(/\d+/);
    return m ? parseInt(m[0], 10) : null;
  };

  const rows = Array.from(document.querySelectorAll('tr.athing'));
  return rows.map((row) => {
    const id = row.getAttribute('id');
    const rankText = row.querySelector('.rank')?.textContent || '';
    const titleLink = row.querySelector('.titleline > a');
    const site = row.querySelector('.sitestr')?.textContent || null;

    // The subtext lives in the immediately following sibling row.
    const subRow = row.nextElementSibling;
    const subtext = subRow ? subRow.querySelector('.subtext') : null;

    const author = subtext?.querySelector('a.hnuser')?.textContent || null;
    const scoreText = subtext?.querySelector('.score')?.textContent || null;

    const ageEl = subtext?.querySelector('.age');
    const ageText = ageEl?.querySelector('a')?.textContent || null;
    const createdAt = ageEl?.getAttribute('title') || null;

    // The comments link is the last anchor pointing at the item page.
    // It reads "N comments", or "discuss" when there are none yet.
    let comments = 0;
    let commentsUrl = id ? `https://news.ycombinator.com/item?id=${id}` : null;
    const itemLinks = subtext
      ? Array.from(subtext.querySelectorAll('a')).filter((a) =>
          (a.getAttribute('href') || '').startsWith('item?id='))
      : [];
    const commentsLink = itemLinks[itemLinks.length - 1];
    if (commentsLink) {
      commentsUrl = commentsLink.href;
      const txt = commentsLink.textContent || '';
      comments = /comment/i.test(txt) ? (toInt(txt) || 0) : 0;
    }

    return {
      id,
      rank: toInt(rankText),
      title: titleLink?.textContent?.trim() || null,
      url: titleLink?.href || null,
      site,
      score: toInt(scoreText),
      author,
      comments,
      comments_url: commentsUrl,
      age: ageText,
      created_at: createdAt,
    };
  });
}
"""


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
