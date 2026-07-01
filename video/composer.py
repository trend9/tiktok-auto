"""
Video Composer — assembles background videos, audio, and text overlays
into a final 9:16 TikTok-ready MP4 using MoviePy 2.x.
"""

import logging
import platform
import subprocess
import textwrap
from pathlib import Path

from moviepy import (
    AudioFileClip,
    ColorClip,
    CompositeVideoClip,
    CompositeAudioClip,
    TextClip,
    VideoFileClip,
    concatenate_audioclips,
    concatenate_videoclips,
)
from moviepy.audio.fx import MultiplyVolume, AudioLoop

import random

import config

logger = logging.getLogger(__name__)

# ── Font helpers ───────────────────────────────────────────────

def _find_font() -> str:
    """Locate a suitable .ttf font file.

    Checks project assets/fonts first, then common system paths.
    """
    # 1. Project fonts directory
    for ttf in config.FONTS_DIR.glob("*.ttf"):
        logger.info("Using project font: %s", ttf)
        return str(ttf)
    for otf in config.FONTS_DIR.glob("*.otf"):
        logger.info("Using project font: %s", otf)
        return str(otf)

    # 2. System fonts (platform-specific)
    system = platform.system()
    candidates: list[Path] = []

    if system == "Windows":
        fonts_dir = Path("C:/Windows/Fonts")
        candidates = [
            fonts_dir / "arial.ttf",
            fonts_dir / "calibri.ttf",
            fonts_dir / "segoeui.ttf",
        ]
    elif system == "Linux":
        # Ubuntu / Debian — DejaVu is almost always available
        candidates = [
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
            Path("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"),
        ]
    elif system == "Darwin":
        candidates = [
            Path("/System/Library/Fonts/Helvetica.ttc"),
            Path("/Library/Fonts/Arial.ttf"),
        ]

    for c in candidates:
        if c.exists():
            logger.info("Using system font: %s", c)
            return str(c)

    # 3. Last resort — let MoviePy/Pillow try its default
    logger.warning("No .ttf font found; falling back to Pillow default.")
    return "Helvetica"


# ── Scene clip builder ─────────────────────────────────────────

def _build_scene_clip(
    scene: dict,
    font: str,
    idx: int,
    total_scenes: int,
    palette: dict,
) -> CompositeVideoClip:
    """Build a single scene: background + text overlay + audio."""

    audio_path = Path(scene["audio_path"])
    audio_clip = AudioFileClip(str(audio_path))
    # Randomize padding to vary video lengths
    padding = random.uniform(0.5, 2.5)
    scene_duration = audio_clip.duration + padding

    # ── Background ──────────────────────────────────────────
    video_path = scene.get("video_path")
    if video_path and Path(video_path).exists():
        try:
            bg = VideoFileClip(str(video_path))

            # Crop to 9:16 aspect ratio
            w, h = bg.size
            target_ratio = config.VIDEO_WIDTH / config.VIDEO_HEIGHT
            current_ratio = w / h

            if current_ratio > target_ratio:
                # Too wide → crop sides
                new_w = int(h * target_ratio)
                x_center = w / 2
                bg = bg.cropped(
                    x1=x_center - new_w / 2,
                    y1=0,
                    x2=x_center + new_w / 2,
                    y2=h,
                )
            else:
                # Too tall → crop top/bottom
                new_h = int(w / target_ratio)
                y_center = h / 2
                bg = bg.cropped(
                    x1=0,
                    y1=y_center - new_h / 2,
                    x2=w,
                    y2=y_center + new_h / 2,
                )

            bg = bg.resized((config.VIDEO_WIDTH, config.VIDEO_HEIGHT))

            # Loop or trim to match scene duration
            if bg.duration < scene_duration:
                bg = bg.with_effects([
                    # moviepy 2.x: loop via time_func
                ])
                # Simple loop: repeat the clip
                loops_needed = int(scene_duration / bg.duration) + 1
                bg = concatenate_videoclips([bg] * loops_needed)

            bg = bg.subclipped(0, scene_duration)

        except Exception as exc:
            logger.warning("Failed to load background video: %s — using black", exc)
            bg = ColorClip(
                size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
                color=(15, 15, 25),
            ).with_duration(scene_duration)
    else:
        # Fallback: dark background
        bg = ColorClip(
            size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
            color=(15, 15, 25),
        ).with_duration(scene_duration)

    # ── Cinematic Tint (Color Grading) ────────────
    overlay = ColorClip(
        size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
        color=config.TINT_COLOR,
    ).with_duration(scene_duration).with_opacity(config.TINT_OPACITY)

    # ── Text overlay ────────────────────────────────────────
    text = scene["text"]
    wrapped_text = "\n".join(textwrap.wrap(text, width=22))
    
    is_author_scene = idx == total_scenes - 1  # Last scene = author

    if is_author_scene:
        font_size = config.AUTHOR_FONT_SIZE
        y_pos = config.VIDEO_HEIGHT * 0.55
    else:
        font_size = config.FONT_SIZE
        y_pos = "center"

    txt_clip = TextClip(
        text=wrapped_text,
        font=font,
        font_size=font_size,
        color=palette["font"],
        stroke_color=palette["stroke"],
        stroke_width=config.STROKE_WIDTH,
        text_align="center",
        interline=15,
        margin=(20, 20),
    )
    
    # Calculate exact positions for drop shadow offset
    w, h = txt_clip.size
    x_center = (config.VIDEO_WIDTH - w) / 2
    y_center = (config.VIDEO_HEIGHT - h) / 2 if y_pos == "center" else y_pos
    
    # Randomize text effect (e.g. fade in duration)
    fade_duration = random.choice([0.0, 0.5, 1.0, 1.5])
    
    txt_clip = txt_clip.with_duration(scene_duration).with_position((x_center, y_center))
    if fade_duration > 0:
        from moviepy.video.fx import FadeIn
        txt_clip = txt_clip.with_effects([FadeIn(duration=fade_duration)])
    
    shadow_clip = TextClip(
        text=wrapped_text,
        font=font,
        font_size=font_size,
        color=palette["shadow"],
        text_align="center",
        interline=15,
        margin=(20, 20),
    ).with_duration(scene_duration).with_position((x_center + config.DROP_SHADOW_OFFSET[0], y_center + config.DROP_SHADOW_OFFSET[1]))
    
    if fade_duration > 0:
        from moviepy.video.fx import FadeIn
        shadow_clip = shadow_clip.with_effects([FadeIn(duration=fade_duration)])

    # ── Compose ─────────────────────────────────────────────
    composite = CompositeVideoClip(
        [bg, overlay, shadow_clip, txt_clip],
        size=(config.VIDEO_WIDTH, config.VIDEO_HEIGHT),
    ).with_duration(scene_duration)

    # Attach audio
    composite = composite.with_audio(audio_clip)

    return composite


# ── Public API ─────────────────────────────────────────────────

def compose_video(scenes: list[dict], output_path: Path) -> Path:
    """Assemble all scenes into a final 9:16 MP4.

    Parameters
    ----------
    scenes : list[dict]
        Scene dicts enriched with ``audio_path``, ``audio_duration``,
        and ``video_path``.
    output_path : Path
        Where to write the final .mp4 file.

    Returns
    -------
    Path
        The *output_path* on success.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    font = _find_font()
    total = len(scenes)
    
    import random
    palette = random.choice(config.TELOP_PALETTES)

    logger.info("Composing %d scenes → %s", total, output_path)
    logger.info("Using telop palette: %s", palette)

    clips: list[CompositeVideoClip] = []
    for idx, scene in enumerate(scenes):
        logger.info("  Building scene %d/%d: '%s…'", idx + 1, total, scene["text"][:30])
        clip = _build_scene_clip(scene, font, idx, total, palette)
        clips.append(clip)

    # Concatenate all scenes
    final = concatenate_videoclips(clips, method="compose")

    # ── Add Background Ambient Audio ────────────────────────────
    # Look for any audio file in assets/audio
    bgm_files = list(config.ASSETS_DIR.glob("audio/*.*"))
    if bgm_files and final.audio is not None:
        bgm_path = random.choice(bgm_files)
        try:
            logger.info("Adding random BGM: %s", bgm_path.name)
            bgm_clip = AudioFileClip(str(bgm_path))
            # Loop background audio to match video length
            bgm_clip = bgm_clip.with_effects([
                AudioLoop(duration=final.duration),
                MultiplyVolume(config.BGM_VOLUME)
            ])
            # Mix TTS audio with BGM
            mixed_audio = CompositeAudioClip([final.audio, bgm_clip])
            final = final.with_audio(mixed_audio)
        except Exception as e:
            logger.warning("Failed to apply BGM: %s", e)

    # Write output
    logger.info("Encoding final video (%.1fs) …", final.duration)
    final.write_videofile(
        str(output_path),
        fps=config.VIDEO_FPS,
        codec=config.VIDEO_CODEC,
        audio_codec=config.AUDIO_CODEC,
        preset="medium",
        threads=2,
        logger=None,  # suppress moviepy's verbose bar in CI
    )

    # Cleanup
    for clip in clips:
        clip.close()
    final.close()

    logger.info("Video saved: %s (%.1f MB)", output_path, output_path.stat().st_size / 1e6)
    return output_path
