"""
Theme Generator — uses Google Gemini API (google-genai SDK) to produce
unique motivational quote themes for TikTok videos.

Reads generation history to avoid duplicates and appends new entries.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from google import genai

import config

logger = logging.getLogger(__name__)


def _load_history() -> list[dict]:
    """Load the generation history from disk."""
    if not config.HISTORY_FILE.exists():
        return []
    with open(config.HISTORY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("generated", [])


def _save_history(entries: list[dict]) -> None:
    """Persist generation history to disk."""
    config.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(config.HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump({"generated": entries}, f, indent=2, ensure_ascii=False)


def _past_themes_summary(history: list[dict], max_items: int = 50) -> str:
    """Build a compact summary of past themes so the LLM can avoid them."""
    if not history:
        return "No previous themes."
    recent = history[-max_items:]
    lines = [f"- {entry.get('theme', 'N/A')}" for entry in recent]
    return "\n".join(lines)


# ── Public API ─────────────────────────────────────────────────

def generate_theme() -> dict:
    """Generate a unique motivational-quote theme via Gemini.

    Returns
    -------
    dict
        {
            "id": "vid_20260626_001",
            "date": "2026-06-26",
            "theme": "...",
            "quote": "...",
            "author": "...",
        }
    """
    if not config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to .env or GitHub Secrets.")

    client = genai.Client(api_key=config.GEMINI_API_KEY)

    history = _load_history()
    past = _past_themes_summary(history)

    prompt = f"""You are a creative content producer for a TikTok channel that posts
motivational and inspirational short videos (under 60 seconds) for an
English-speaking audience.

Generate ONE unique theme with a powerful quote.  The quote should be
either a famous quote with its real author, or an original inspirational
quote (mark author as "Unknown" if original).

IMPORTANT — the following themes have already been used.  Do NOT repeat
any of them or anything too similar:
{past}

Respond in **valid JSON only** (no markdown fences, no extra text):
{{
  "theme": "<short theme title, e.g. Resilience in Adversity>",
  "quote": "<the full quote text>",
  "author": "<author name or Unknown>"
}}
"""

    logger.info("Requesting theme from Gemini API …")
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt,
    )
    raw = response.text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Gemini returned invalid JSON: %s", raw)
        raise ValueError(f"Invalid JSON from Gemini: {raw}")

    # Validate required keys
    for key in ("theme", "quote", "author"):
        if key not in result:
            raise ValueError(f"Missing key '{key}' in Gemini response: {result}")

    # Build the history entry
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    count_today = sum(1 for e in history if e.get("date") == date_str) + 1
    entry_id = f"vid_{date_str.replace('-', '')}_{count_today:03d}"

    entry = {
        "id": entry_id,
        "date": date_str,
        "theme": result["theme"],
        "quote": result["quote"],
        "author": result["author"],
        "status": "theme_generated",
    }

    # Persist immediately so the next call won't duplicate
    history.append(entry)
    _save_history(history)

    logger.info("Theme generated: %s — %s", entry["theme"], entry["id"])
    return entry
