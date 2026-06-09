"""Pure constants for Hacker News extraction (no third-party imports).

Kept import-free so it can be reused by both the Intuned API code and the
standalone local runner without pulling in the Intuned runtime.
"""

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
