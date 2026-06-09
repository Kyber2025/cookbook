"""Send messages to Telegram via the Bot API.

Configure via env vars:
  TELEGRAM_BOT_TOKEN        - bot token (required)
  TELEGRAM_APPROVAL_CHAT_ID - target chat id to send to (required)
  TELEGRAM_API_BASE_URL     - API base (default: https://api.telegram.org)
"""

import html
import os

import httpx

TELEGRAM_MAX_LEN = 4096


def _chunk(text: str, size: int = TELEGRAM_MAX_LEN) -> list[str]:
    """Split text into Telegram-sized chunks, preferring line boundaries."""
    if len(text) <= size:
        return [text]
    chunks, current = [], ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > size:
            if current:
                chunks.append(current)
            # A single over-long line is hard-split.
            while len(line) > size:
                chunks.append(line[:size])
                line = line[size:]
            current = line
        else:
            current = f"{current}\n{line}" if current else line
    if current:
        chunks.append(current)
    return chunks


def build_digest_message(stories: list[dict], header: str) -> str:
    """Render the enriched stories into an HTML-formatted Telegram message."""
    lines = [f"<b>{html.escape(header)}</b>", ""]

    # Group by category for a tidier digest.
    by_category: dict[str, list[dict]] = {}
    for s in stories:
        by_category.setdefault(s.get("category") or "其他", []).append(s)

    for category, items in by_category.items():
        lines.append(f"\n<b>📂 {html.escape(category)}</b>")
        for s in items:
            rank = s.get("rank")
            title_zh = s.get("title_zh") or s.get("title") or "(无标题)"
            title_en = s.get("title") or ""
            url = s.get("url") or s.get("comments_url") or ""
            score = s.get("score") if s.get("score") is not None else 0
            comments = s.get("comments") if s.get("comments") is not None else 0
            summary = s.get("summary_zh") or ""

            title_line = f"<b>{rank}. <a href=\"{html.escape(url)}\">{html.escape(title_zh)}</a></b>"
            lines.append(f"\n{title_line}")
            if title_en and title_en != title_zh:
                lines.append(f"<i>{html.escape(title_en)}</i>")
            if summary:
                lines.append(html.escape(summary))
            lines.append(
                f"🔼 {score} 分 · 💬 {comments} 评论 · "
                f"<a href=\"{html.escape(s.get('comments_url') or '')}\">讨论</a>"
            )

    return "\n".join(lines)


async def send_message(text: str) -> list[dict]:
    """Send `text` to the configured Telegram chat, splitting if needed.

    Returns the list of Telegram API responses. Raises if credentials are
    missing or the API returns an error.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_APPROVAL_CHAT_ID")
    base_url = os.environ.get("TELEGRAM_API_BASE_URL", "https://api.telegram.org").rstrip("/")

    if not token or not chat_id:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN and TELEGRAM_APPROVAL_CHAT_ID must be set to send messages"
        )

    url = f"{base_url}/bot{token}/sendMessage"
    responses = []
    async with httpx.AsyncClient(timeout=30) as client:
        for chunk in _chunk(text):
            resp = await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            if not data.get("ok"):
                raise RuntimeError(f"Telegram API error: {data}")
            responses.append(data)
    return responses
