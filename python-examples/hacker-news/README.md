# Hacker News Daily Digest → Telegram (Python)

Scrape the [Hacker News](https://news.ycombinator.com/) front page, use an LLM
(**gpt-5.4**) to **translate each title into Chinese, classify it, and write a
one-line Chinese summary**, then push a grouped digest to **Telegram** — every
morning at **09:00**.

Two APIs are included:

- **`scrape-front-page`** — just scrape the front page (rank, title, link, score, author, comments, age, timestamp) and print/return JSON.
- **`daily-digest`** — scrape → LLM translate/classify/summarize (Chinese) → push to Telegram. This is the one scheduled daily.

<!-- IDE-IGNORE-START -->
## Run on Intuned

<a href="https://app.intuned.io?repo=https://github.com/Intuned/cookbook/tree/main/python-examples/hacker-news" target="_blank" rel="noreferrer"><img src="https://cdn1.intuned.io/button.svg" alt="Run on Intuned"></a>
<!-- IDE-IGNORE-END -->

## How it works

```text
scrape HN front page  ──►  LLM (gpt-5.4)            ──►  Telegram Bot API
(single DOM pass)          • 中文标题翻译                sendMessage
                           • 分类 (AI/编程/创业/…)        (HTML, grouped by
                           • 一句话中文摘要               category, chunked)
```

Hacker News renders each story as a `tr.athing` row, with metadata (score,
author, comments) in the following sibling row. The scraper runs a single
in-browser DOM pass (`page.evaluate`) over all rows — avoiding dozens of
Playwright round-trips and staying resilient to missing fields (job posts have
no score/author/comments). The LLM enrichment is done in **one batched call**
for all stories and returns structured JSON. The Telegram message is grouped by
category and split into ≤4096-char chunks.

## APIs

### `daily-digest`

Scrape → translate/classify/summarize in Chinese → push to Telegram.

| Parameter | Type | Default | Description |
| --------- | ---- | ------- | ----------- |
| `pages` | int | 1 | Listing pages to scrape (each ~30 stories). |
| `limit` | int | 10 | Number of top stories to translate + push. |
| `send` | bool | true | Send to Telegram. Set `false` for a dry run (print only). |

### `scrape-front-page`

Scrape only — prints and returns the raw stories.

| Parameter | Type | Default | Description |
| --------- | ---- | ------- | ----------- |
| `pages` | int | 1 | Listing pages to scrape (each ~30 stories). `1` = top 30. |

## Project Structure

```text
hacker-news/
├── api/
│   ├── daily-digest.py             # Scrape → LLM enrich → push to Telegram
│   └── scrape-front-page.py        # Scrape-only API
├── utils/
│   ├── __init__.py
│   ├── hn.py                       # HN scraping (single-DOM-pass extraction)
│   ├── llm.py                      # OpenAI-compatible Chinese translate/classify/summarize
│   └── telegram.py                 # Telegram Bot API message build + send
├── intuned-resources/
│   └── jobs/
│       └── daily-digest.job.jsonc  # Job payload for the daily run
├── .parameters/api/
│   ├── daily-digest/default.json
│   └── scrape-front-page/default.json
├── .env.example                    # Copy to .env and fill in secrets
├── Intuned.jsonc
└── README.md
```

## Envs

Copy `.env.example` to `.env` and fill in your values. **`.env` is gitignored — never commit it.**

| Variable | Required | Description |
| -------- | -------- | ----------- |
| `OPENAI_API_KEY` | yes (for digest) | OpenAI (or compatible) API key used for translation/classification/summary. |
| `OPENAI_MODEL` | no | LLM model. Default `gpt-5.4`. |
| `OPENAI_BASE_URL` | no | OpenAI-compatible API base. Default `https://api.openai.com/v1`. |
| `TELEGRAM_BOT_TOKEN` | yes (for digest) | Telegram bot token from @BotFather. |
| `TELEGRAM_APPROVAL_CHAT_ID` | yes (for digest) | Chat/group/channel id the digest is sent to. |
| `TELEGRAM_API_BASE_URL` | no | Telegram API base. Default `https://api.telegram.org`. |
| `TELEGRAM_WEBHOOK_SECRET` | no | Only needed if you add a Telegram webhook/approval flow on top of this. |
| `INTUNED_API_KEY` | for deploy/jobs | Intuned API key. Not needed for local `intuned dev run`. |

> If `OPENAI_API_KEY` is missing or the LLM call fails, the digest degrades
> gracefully — it still sends the (untranslated) stories instead of crashing.

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

### Run the digest (dry run — no Telegram send)

```bash
intuned dev run api daily-digest .parameters/api/daily-digest/default.json --headless
```

Edit `.parameters/api/daily-digest/default.json` and set `"send": false` to
preview the message without pushing, or `"send": true` to actually push.

### Run the scraper only

```bash
intuned dev run api scrape-front-page .parameters/api/scrape-front-page/default.json --headless
```
<!-- IDE-IGNORE-END -->

## Running daily (every morning at 09:00)

The job at `intuned-resources/jobs/daily-digest.job.jsonc` defines the payload.
To run it once per day at 09:00, create a **scheduled Job/Trigger** on the
Intuned platform with cron `0 9 * * *` (adjust for your timezone) pointing at
this job — the schedule lives on the platform, not in the job file. See the
[Jobs documentation](https://intunedhq.com/docs/main/02-features/jobs-batched-executions).

You can also trigger a run via the API:

```bash
curl -X POST "https://api.intunedhq.com/projects/{project}/jobs" \
  -H "Authorization: Bearer {api_key}" \
  -d '{
    "payload": {
      "api": "daily-digest",
      "parameters": { "pages": 1, "limit": 10, "send": true }
    }
  }'
```

## Related

- [Intuned CLI](https://intunedhq.com/docs/main/05-references/cli/overview)
- [Intuned Browser SDK](https://intunedhq.com/docs/automation-sdks/overview)
- [Intuned Jobs Documentation](https://intunedhq.com/docs/main/02-features/jobs-batched-executions)
- [Telegram Bot API](https://core.telegram.org/bots/api#sendmessage)
