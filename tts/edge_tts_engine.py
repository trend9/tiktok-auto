"""
Edge-TTS engine — uses Microsoft Edge's free online TTS service.

No API key required.  Supports high-quality English neural voices.
"""

import asyncio
import logging
from pathlib import Path

import edge_tts
from mutagen.mp3 import MP3

import config
from tts.tts_base import TTSBase

logger = logging.getLogger(__name__)


class EdgeTTSEngine(TTSBase):
    """TTS engine backed by Edge-TTS (``edge-tts`` package)."""

    def __init__(self, voice: str | None = None):
        self.voice = voice or config.TTS_VOICE

    async def synthesize(self, text: str, output_path: Path) -> float:
        """Generate an MP3 file from *text* and return its duration."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Edge-TTS: synthesizing '%s…' → %s", text[:40], output_path.name)

        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(str(output_path))

        # Read back the duration using mutagen
        audio = MP3(str(output_path))
        duration = audio.info.length
        logger.info("  → duration: %.2fs", duration)
        return duration


# ── Convenience wrappers for synchronous callers ───────────────

def synthesize_sync(text: str, output_path: Path, voice: str | None = None) -> float:
    """Synchronous wrapper around :meth:`EdgeTTSEngine.synthesize`."""
    engine = EdgeTTSEngine(voice=voice)
    return asyncio.run(engine.synthesize(text, output_path))


async def synthesize_scenes(
    scenes: list[dict],
    temp_dir: Path,
    voice: str | None = None,
) -> list[dict]:
    """Synthesize audio for every scene and return enriched scene dicts.

    Each scene dict gets two new keys:
    - ``audio_path``: Path to the generated MP3.
    - ``audio_duration``: Actual duration in seconds.
    """
    engine = EdgeTTSEngine(voice=voice)
    enriched: list[dict] = []

    for idx, scene in enumerate(scenes):
        out = temp_dir / f"scene_{idx:03d}.mp3"
        duration = await engine.synthesize(scene["text"], out)
        enriched.append(
            {
                **scene,
                "audio_path": str(out),
                "audio_duration": duration,
            }
        )

    return enriched
