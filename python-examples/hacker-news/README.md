# Hacker News Daily Scraper (Python)

Scrape the [Hacker News](https://news.ycombinator.com/) front page on a daily
schedule. For each story it extracts the **rank, title, link, score, author,
comments count, comments URL, posting age and absolute timestamp**, prints the
results, and returns them as structured JSON.

<!-- IDE-IGNORE-START -->
## Run on Intuned

<a href="https://app.intuned.io?repo=https://github.com/Intuned/cookbook/tree/main/python-examples/hacker-news" target="_blank" rel="noreferrer"><img src="https://cdn1.intuned.io/button.svg" alt="Run on Intuned"></a>
<!-- IDE-IGNORE-END -->

## How it works

Hacker News renders each story as a `tr.athing` row, with the metadata (score,
author, comments) in the immediately following sibling row. The scraper runs a
single in-browser DOM pass (`page.evaluate`) over all rows on the page — this
avoids dozens of Playwright round-trips and stays resilient to missing fields
(job posts have no score/author/comments). Set `pages` > 1 to follow the
**More** link and scrape additional listing pages (~30 stories each).

## API

### `scrape-front-page`

Scrapes the Hacker News front page and prints + returns the stories.

| Parameter | Type | Default | Description |
| --------- | ---- | ------- | ----------- |
| `pages` | int | 1 | Number of listing pages to scrape (each ~30 stories). `1` = top 30. |

**Returns**

```json
{
  "source": "https://news.ycombinator.com/",
  "pages_scraped": 1,
  "count": 30,
  "stories": [
    {
      "id": "12345678",
      "rank": 1,
      "title": "Show HN: My new project",
      "url": "https://example.com/article",
      "site": "example.com",
      "score": 256,
      "author": "pg",
      "comments": 87,
      "comments_url": "https://news.ycombinator.com/item?id=12345678",
      "age": "3 hours ago",
      "created_at": "2026-06-09T10:00:00"
    }
  ]
}
```

## Project Structure

```text
hacker-news/
├── api/
│   └── scrape-front-page.py        # Main API: scrape HN front page stories
├── intuned-resources/
│   └── jobs/
│       └── scrape-front-page.job.jsonc  # Job payload for the daily run
├── .parameters/api/
│   └── scrape-front-page/
│       └── default.json            # Default parameters for local runs
├── .env.example
├── Intuned.jsonc                   # Intuned project configuration
└── README.md
```

<!-- IDE-IGNORE-START -->
## Getting Started

### Install dependencies

```bash
uv sync
```

If the `intuned` CLI is not installed, install it globally:

```bash
npm install -g @intuned/cli
```

After installing dependencies, the `intuned` command should be available in your
environment.

### Run an API

```bash
intuned dev run api scrape-front-page .parameters/api/scrape-front-page/default.json
```

Run headless (no visible browser window):

```bash
intuned dev run api scrape-front-page .parameters/api/scrape-front-page/default.json --headless
```

Scrape more than the top 30 by editing `.parameters/api/scrape-front-page/default.json`:

```json
{
  "pages": 3
}
```
<!-- IDE-IGNORE-END -->

## Running daily

This project ships a job definition at
`intuned-resources/jobs/scrape-front-page.job.jsonc` that runs the
`scrape-front-page` API. To run it **once per day**, create a scheduled Job /
Trigger on the Intuned platform and point it at this job — the schedule (cron,
e.g. `0 13 * * *` for 13:00 UTC daily) is configured on the platform, not in
this file. See the
[Jobs documentation](https://intunedhq.com/docs/main/02-features/jobs-batched-executions)
for scheduling details.

You can also trigger a job run via the API:

```bash
curl -X POST "https://api.intunedhq.com/projects/{project}/jobs" \
  -H "Authorization: Bearer {api_key}" \
  -d '{
    "payload": {
      "api": "scrape-front-page",
      "parameters": { "pages": 1 }
    },
    "sink": {
      "type": "webhook",
      "url": "https://your-webhook.com/results"
    }
  }'
```

## Envs

| Variable | Required | Description |
| -------- | -------- | ----------- |
| `INTUNED_API_KEY` | For deploy/job runs | Your Intuned API key. Not needed for local `intuned dev run` against a provisioned project. |

## Related

- [Intuned CLI](https://intunedhq.com/docs/main/05-references/cli/overview)
- [Intuned Browser SDK](https://intunedhq.com/docs/automation-sdks/overview)
- [Intuned Jobs Documentation](https://intunedhq.com/docs/main/02-features/jobs-batched-executions)
- [Intuned llm.txt](https://intunedhq.com/docs/llms.txt)
