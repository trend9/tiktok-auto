"""
TikTok Auto Video Generator — main entry point.

Orchestrates the full pipeline:
  1. Generate theme + quote         (Gemini API)
  2. Generate scenario              (Gemini API)
  3. Validate scenario              (Stage 1)
  4. Synthesize audio               (Edge-TTS)
  5. Download background videos     (Pexels API)
  6. Validate assets                (Stage 2)
  7. Compose final video            (MoviePy)
  8. Validate output                (Stage 3)
  9. Update history
"""

import argparse
import asyncio
import json
import logging
import shutil
import sys
from pathlib import Path

import config
from generators.theme_generator import generate_theme
from generators.scenario_generator import generate_scenario
from tts.edge_tts_engine import synthesize_scenes
from media.pexels_client import fetch_videos_for_scenes
from video.validator import validate_scenario, validate_assets, validate_output
from video.composer import compose_video

# ── Logging setup ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")

MAX_RETRIES = 3


def _update_history_status(video_id: str, status: str) -> None:
    """Update the status field for a given video in the history file."""
    if not config.HISTORY_FILE.exists():
        return
    with open(config.HISTORY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for entry in data.get("generated", []):
        if entry.get("id") == video_id:
            entry["status"] = status
            break
    with open(config.HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def generate_one_video(voice: str | None = None, theme_override: str | None = None) -> Path | None:
    """Run the full pipeline for one video.

    Returns the output Path on success, or None on failure.
    """
    video_id: str | None = None

    try:
        # ── Step 1 & 2: Theme & Scenario ───────────────────────────────
        theme_entry = None
        scenario = None

        for attempt in range(1, MAX_RETRIES + 1):
            if theme_entry is None:
                logger.info("=" * 60)
                logger.info("STEP 1 — Generating theme (attempt %d) …", attempt)
                theme_entry = generate_theme()
                video_id = theme_entry["id"]
                logger.info("  Theme: %s", theme_entry["theme"])
                logger.info("  Quote: %s", theme_entry["quote"])

            logger.info("STEP 2 — Generating scenario (attempt %d) …", attempt)
            scenario = generate_scenario(theme_entry)

            # ── Step 3: Validate scenario ──────────────────
            logger.info("STEP 3 — Validating scenario (attempt %d) …", attempt)
            errors = validate_scenario(scenario)
            if not errors:
                break
                
            logger.warning("  Scenario issues: %s — retrying …", errors)
            if any("Duplicate theme" in e for e in errors):
                # Must generate a new theme next attempt
                _update_history_status(video_id, "duplicate_theme")
                theme_entry = None
                
            scenario = None

        if scenario is None:
            logger.error("Failed to generate a valid scenario after %d retries.", MAX_RETRIES)
            if video_id:
                _update_history_status(video_id, "failed_scenario")
            return None

        scenes = scenario["scenes"]

        # ── Step 4: TTS audio ──────────────────────────────
        logger.info("STEP 4 — Synthesizing audio (%d scenes) …", len(scenes))
        work_dir = config.TEMP_DIR / video_id
        work_dir.mkdir(parents=True, exist_ok=True)

        import random
        # Randomize voice if not explicitly provided
        actual_voice = voice
        if not actual_voice:
            actual_voice = random.choice(config.AVAILABLE_VOICES)
        
        # Randomize speed (+/- 15%) and pitch (+/- 10Hz) to sound less AI-like
        rate_val = random.randint(-15, 15)
        pitch_val = random.randint(-10, 10)
        rate_str = f"{rate_val:+d}%"
        pitch_str = f"{pitch_val:+d}Hz"
        
        logger.info("  Using TTS Voice: %s, Rate: %s, Pitch: %s", actual_voice, rate_str, pitch_str)

        scenes = asyncio.run(synthesize_scenes(
            scenes, 
            work_dir, 
            voice=actual_voice, 
            rate=rate_str, 
            pitch=pitch_str
        ))

        # ── Step 5: Background videos ──────────────────────
        logger.info("STEP 5 — Downloading background videos …")
        scenes = fetch_videos_for_scenes(scenes, work_dir)

        # ── Step 6: Validate assets ────────────────────────
        logger.info("STEP 6 — Validating assets …")
        asset_errors = validate_assets(scenes)
        if asset_errors:
            logger.error("Asset validation failed: %s", asset_errors)
            _update_history_status(video_id, "failed_assets")
            return None

        # ── Step 7: Compose video ──────────────────────────
        logger.info("STEP 7 — Composing video …")
        import re
        safe_title = re.sub(r'[^a-zA-Z0-9_\- ]', '', scenario.get("title", "video")).strip()
        safe_title = safe_title.replace(' ', '_')
        if not safe_title:
            safe_title = f"video_{video_id}"
        output_path = config.OUTPUT_DIR / f"{safe_title}.mp4"
        compose_video(scenes, output_path)

        # ── Step 8: Final validation ───────────────────────
        logger.info("STEP 8 — Final validation …")
        output_errors = validate_output(output_path)
        if output_errors:
            logger.error("Output validation failed: %s", output_errors)
            _update_history_status(video_id, "failed_output")
            return None

        # ── Step 8.5: Write description text for manual posting ────────────
        logger.info("STEP 8.5 — Writing description text …")
        description_text = f"{scenario.get('title', '')}\n\n\"{theme_entry.get('quote', '')}\"\n\n#motivation #success #mindset #shorts"
        
        meta_path = config.OUTPUT_DIR / f"{output_path.stem}.txt"
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(description_text)

        # ── Step 9: Mark as completed ──────────────────────
        _update_history_status(video_id, "completed")
        logger.info("✅  Video completed: %s", output_path)

        # Cleanup temp files
        shutil.rmtree(work_dir, ignore_errors=True)

        return output_path

    except Exception:
        logger.exception("Unexpected error during video generation")
        if video_id:
            _update_history_status(video_id, "error")
        return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TikTok Auto Video Generator — create motivational short videos",
    )
    parser.add_argument(
        "--count", "-n",
        type=int,
        default=1,
        help="Number of videos to generate (default: 1)",
    )
    parser.add_argument(
        "--voice", "-v",
        type=str,
        default=None,
        help=f"Edge-TTS voice (default: {config.TTS_VOICE})",
    )
    parser.add_argument(
        "--theme", "-t",
        type=str,
        default=None,
        help="Override theme (not yet implemented — reserved)",
    )
    args = parser.parse_args()

    # Preflight checks
    if not config.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set.  Add it to .env or set as env var.")
        sys.exit(1)
    if not config.PEXELS_API_KEY:
        logger.error("PEXELS_API_KEY is not set.  Add it to .env or set as env var.")
        sys.exit(1)

    logger.info("Starting batch: %d video(s) requested", args.count)

    successes = 0
    failures = 0

    for i in range(args.count):
        logger.info("━" * 60)
        logger.info("Video %d / %d", i + 1, args.count)
        logger.info("━" * 60)
        result = generate_one_video(voice=args.voice)
        if result:
            successes += 1
        else:
            failures += 1
            
        if i < args.count - 1:
            logger.info("Waiting 15 seconds before next video to avoid rate limits...")
            import time
            time.sleep(15)

    logger.info("━" * 60)
    logger.info("Batch complete: %d succeeded, %d failed", successes, failures)

    if failures > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
