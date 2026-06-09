"""LLM enrichment: Chinese translation, classification and summary.

Uses the OpenAI-compatible Chat Completions API. Configure via env vars:
  OPENAI_API_KEY   - API key (required)
  OPENAI_MODEL     - model name (default: gpt-5.4)
  OPENAI_BASE_URL  - API base, OpenAI-compatible (default: https://api.openai.com/v1)
"""

import json
import os

import httpx

DEFAULT_MODEL = "gpt-5.4"
DEFAULT_BASE_URL = "https://api.openai.com/v1"

# Categories the model must choose from, so downstream grouping is stable.
CATEGORIES = [
    "AI/机器学习",
    "编程/软件开发",
    "创业/商业",
    "安全/隐私",
    "硬件/芯片",
    "科学/研究",
    "互联网/产品",
    "其他",
]

SYSTEM_PROMPT = (
    "你是一名中文科技资讯编辑。给定一组 Hacker News 头条，"
    "为每条新闻：1) 把标题翻译成简洁自然的中文；2) 从给定类别中选择最合适的一个分类；"
    "3) 基于标题（以及站点信息）写一句 30~60 字的中文摘要，说明这条新闻大概在讲什么。"
    f"分类只能从以下列表中选择：{', '.join(CATEGORIES)}。"
    '严格只输出 JSON，格式为 {"items": [{"rank": <int>, "title_zh": <str>, '
    '"category": <str>, "summary_zh": <str>}]}，每条对应输入中的 rank。'
)


def _build_user_payload(stories: list[dict]) -> str:
    compact = [
        {
            "rank": s.get("rank"),
            "title": s.get("title"),
            "site": s.get("site"),
        }
        for s in stories
    ]
    return json.dumps({"stories": compact}, ensure_ascii=False)


async def enrich_stories(stories: list[dict]) -> list[dict]:
    """
    Translate, classify and summarize stories in Chinese in a single LLM call.

    Returns a new list where each story gains `title_zh`, `category` and
    `summary_zh`. If the API key is missing or the call fails, the stories are
    returned unchanged (with empty enrichment fields) so the pipeline degrades
    gracefully instead of crashing.
    """
    if not stories:
        return stories

    api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", DEFAULT_MODEL)
    base_url = os.environ.get("OPENAI_BASE_URL", DEFAULT_BASE_URL).rstrip("/")

    enriched = [dict(s) for s in stories]
    if not api_key:
        print("[llm] OPENAI_API_KEY not set — skipping translation/summary")
        for s in enriched:
            s.setdefault("title_zh", None)
            s.setdefault("category", None)
            s.setdefault("summary_zh", None)
        return enriched

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_payload(stories)},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
    }

    print(f"[llm] enriching {len(stories)} stories with {model} ...")
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json=body,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)
    except Exception as e:  # noqa: BLE001 - degrade gracefully on any failure
        print(f"[llm] enrichment failed ({e!r}) — returning untranslated stories")
        for s in enriched:
            s.setdefault("title_zh", None)
            s.setdefault("category", None)
            s.setdefault("summary_zh", None)
        return enriched

    by_rank = {item.get("rank"): item for item in parsed.get("items", [])}
    for s in enriched:
        item = by_rank.get(s.get("rank"), {})
        s["title_zh"] = item.get("title_zh")
        s["category"] = item.get("category")
        s["summary_zh"] = item.get("summary_zh")

    return enriched
