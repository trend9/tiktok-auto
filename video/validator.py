"""
Three-stage validator for the video generation pipeline.

Stage 1 — Scenario validation  (structure, durations, duplicates)
Stage 2 — Asset validation      (audio files, video files)
Stage 3 — Final output validation (resolution, duration, file size)
"""

import json
import logging
from pathlib import Path

from mutagen.mp3 import MP3

import config

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when a validation step fails."""


# ── Stage 1: Scenario ─────────────────────────────────────────

def validate_scenario(scenario: dict) -> list[str]:
    """Check the scenario dict for structural / content problems.

    Returns a list of error messages (empty = passed).
    """
    errors: list[str] = []

    # Required top-level keys
    for key in ("title", "scenes", "total_duration"):
        if key not in scenario:
            errors.append(f"Missing key: {key}")

    scenes = scenario.get("scenes", [])
    if not scenes:
        errors.append("Scenario has no scenes.")
        return errors

    # Per-scene checks
    total = 0.0
    for i, scene in enumerate(scenes):
        text = scene.get("text", "")
        dur = scene.get("duration", 0)

        if not text.strip():
            errors.append(f"Scene {i}: text is empty.")

        if dur < config.MIN_SCENE_DURATION:
            errors.append(f"Scene {i}: duration {dur}s < minimum {config.MIN_SCENE_DURATION}s.")
        if dur > config.MAX_SCENE_DURATION:
            errors.append(f"Scene {i}: duration {dur}s > maximum {config.MAX_SCENE_DURATION}s.")

        if not scene.get("search_keyword"):
            errors.append(f"Scene {i}: search_keyword is missing.")

        total += dur

    # Total duration
    if total > 60:
        errors.append(f"Total duration {total:.1f}s exceeds 60s limit.")
    if total < 15:
        errors.append(f"Total duration {total:.1f}s is suspiciously short.")

    # Duplicate check against history
    _check_duplicate(scenario, errors)

    if errors:
        logger.warning("Scenario validation FAILED: %s", errors)
    else:
        logger.info("Scenario validation PASSED ✓")

    return errors


def _check_duplicate(scenario: dict, errors: list[str]) -> None:
    """Check whether a very similar title/quote already exists."""
    if not config.HISTORY_FILE.exists():
        return

    with open(config.HISTORY_FILE, "r", encoding="utf-8") as f:
        history = json.load(f).get("generated", [])

    title_lower = scenario.get("title", "").lower()
    for entry in history:
        if entry.get("theme", "").lower() == title_lower and entry.get("status") == "completed":
            errors.append(f"Duplicate theme detected: '{title_lower}' already in history.")
            break


# ── Stage 2: Assets ────────────────────────────────────────────

def validate_assets(scenes: list[dict]) -> list[str]:
    """Verify that all audio and video assets exist and are usable.

    Expects each scene dict to contain ``audio_path`` and ``video_path``.
    """
    errors: list[str] = []

    for i, scene in enumerate(scenes):
        # Audio check
        audio = scene.get("audio_path")
        if not audio or not Path(audio).exists():
            errors.append(f"Scene {i}: audio file missing ({audio}).")
        else:
            try:
                mp3 = MP3(audio)
                if mp3.info.length < 0.1:
                    errors.append(f"Scene {i}: audio file too short ({mp3.info.length:.2f}s).")
            except Exception as exc:
                errors.append(f"Scene {i}: audio file corrupt ({exc}).")

        # Video check
        video = scene.get("video_path")
        if not video or not Path(video).exists():
            errors.append(f"Scene {i}: background video missing ({video}).")
        else:
            size_mb = Path(video).stat().st_size / 1e6
            if size_mb < 0.01:
                errors.append(f"Scene {i}: background video suspiciously small ({size_mb:.2f} MB).")

    if errors:
        logger.warning("Asset validation FAILED: %s", errors)
    else:
        logger.info("Asset validation PASSED ✓")

    return errors


# ── Stage 3: Final output ─────────────────────────────────────

def validate_output(output_path: Path) -> list[str]:
    """Check the final MP4 file for correctness.

    Uses ffprobe-style checks via moviepy to verify resolution,
    duration, and the presence of audio.
    """
    errors: list[str] = []

    if not output_path.exists():
        errors.append(f"Output file does not exist: {output_path}")
        return errors

    # File size
    size_mb = output_path.stat().st_size / 1e6
    if size_mb > config.MAX_FILE_SIZE_MB:
        errors.append(f"File size {size_mb:.1f} MB exceeds {config.MAX_FILE_SIZE_MB} MB limit.")
    if size_mb < 0.05:
        errors.append(f"File size {size_mb:.3f} MB is suspiciously small.")

    # Use moviepy to inspect
    try:
        from moviepy import VideoFileClip

        clip = VideoFileClip(str(output_path))

        w, h = clip.size
        if w != config.VIDEO_WIDTH or h != config.VIDEO_HEIGHT:
            errors.append(f"Resolution {w}×{h} ≠ expected {config.VIDEO_WIDTH}×{config.VIDEO_HEIGHT}.")

        if clip.duration > 60:
            errors.append(f"Duration {clip.duration:.1f}s exceeds 60s.")

        if clip.audio is None:
            errors.append("No audio track found in output.")

        clip.close()

    except Exception as exc:
        errors.append(f"Could not inspect output file: {exc}")

    if errors:
        logger.warning("Output validation FAILED: %s", errors)
    else:
        logger.info("Output validation PASSED ✓")

    return errors
