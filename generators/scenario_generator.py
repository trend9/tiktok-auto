"""
Scenario Generator — takes a theme/quote and produces a timed scene list
suitable for a 9:16 TikTok video (≤ 55 seconds).

Each scene includes the display text, estimated duration,
a Pexels search keyword, and a text animation effect.
"""

import json
import logging

from google import genai

import config

logger = logging.getLogger(__name__)


def generate_scenario(theme_entry: dict) -> dict:
    """Turn a theme entry into a full scenario with timed scenes.

    Parameters
    ----------
    theme_entry : dict
        Output of ``theme_generator.generate_theme()``.

    Returns
    -------
    dict
        {
            "id": "<video id>",
            "title": "...",
            "quote_author": "...",
            "total_duration": 52.0,
            "scenes": [ { "text", "duration", "search_keyword", "text_effect" }, ... ]
        }
    """
    if not config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set.")

    client = genai.Client(api_key=config.GEMINI_API_KEY)

    quote = theme_entry["quote"]
    author = theme_entry["author"]
    theme = theme_entry["theme"]

    prompt = f"""You are a TikTok video scriptwriter.  Given the theme, quote, and
author below, produce a scene-by-scene breakdown for a motivational
short video.

Theme: {theme}
Quote: "{quote}"
Author: {author}

Rules:
1. Split the content into 5-10 scenes.
2. Each scene has a short text line (≤ 15 words) displayed on screen.
3. The first scene should be a hook / attention grabber.
4. The quote itself should be split across 2-4 scenes.
5. The last scene should show the author attribution.
6. Each scene duration must be between {config.MIN_SCENE_DURATION} and {config.MAX_SCENE_DURATION} seconds.
7. Total duration of ALL scenes must be between 45 and {config.MAX_DURATION} seconds.
8. For each scene, provide a search_keyword (1-3 English words) that
   describes an aesthetically pleasing background video for that scene
   (nature, cinematic, abstract, etc.).
9. text_effect must be one of: "fade_in", "slide_up", "typewriter".

Respond in **valid JSON only** (no markdown fences):
{{
  "title": "{theme}",
  "quote_author": "{author}",
  "total_duration": <number>,
  "scenes": [
    {{
      "text": "<display text>",
      "duration": <seconds as float>,
      "search_keyword": "<pexels search term>",
      "text_effect": "fade_in"
    }}
  ]
}}
"""

    logger.info("Requesting scenario from Gemini API …")
    models_to_try = ["gemini-2.5-flash-lite", "gemini-1.5-flash-8b", "gemini-1.5-pro", "gemini-2.0-flash-lite-preview-02-05"]
    last_error = None
    response = None
    
    for model_name in models_to_try:
        try:
            logger.info(f"Trying model: {model_name}")
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            break
        except Exception as e:
            logger.warning(f"Model {model_name} failed: {e}")
            last_error = e
            
    if response is None:
        raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")

    raw = response.text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    try:
        scenario = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Gemini returned invalid JSON for scenario: %s", raw)
        raise ValueError(f"Invalid JSON from Gemini (scenario): {raw}")

    # Inject the video id from the theme entry
    scenario["id"] = theme_entry["id"]

    # Recalculate total_duration from scenes for accuracy
    actual_total = sum(scene["duration"] for scene in scenario["scenes"])
    scenario["total_duration"] = round(actual_total, 1)

    logger.info(
        "Scenario generated: %d scenes, %.1fs total",
        len(scenario["scenes"]),
        scenario["total_duration"],
    )
    return scenario
