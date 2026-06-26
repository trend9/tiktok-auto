"""
Configuration module for TikTok Auto Video Generator.

Loads settings from environment variables or .env file.
For GitHub Actions, secrets are injected automatically.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists (local development)
load_dotenv()

# ── Project Paths ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMP_DIR = PROJECT_ROOT / "temp"
HISTORY_DIR = PROJECT_ROOT / "history"
ASSETS_DIR = PROJECT_ROOT / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"

# Create directories if they don't exist
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)
HISTORY_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)
FONTS_DIR.mkdir(exist_ok=True)

# ── API Keys ───────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
PEXELS_API_KEY: str = os.getenv("PEXELS_API_KEY", "")

# ── Video Settings ─────────────────────────────────────────────
VIDEO_WIDTH: int = 1080
VIDEO_HEIGHT: int = 1920
VIDEO_FPS: int = 24
MAX_DURATION: float = 55.0  # seconds (keep under 60s)
VIDEO_CODEC: str = "libx264"
AUDIO_CODEC: str = "aac"

# ── TTS Settings ───────────────────────────────────────────────
TTS_VOICE: str = os.getenv("TTS_VOICE", "en-US-GuyNeural")

# Available English voices for Edge-TTS:
#   en-US-GuyNeural       - Calm male (recommended for quotes)
#   en-US-JennyNeural     - Clear female
#   en-GB-RyanNeural      - British male
#   en-US-AriaNeural      - Expressive female
#   en-US-DavisNeural     - Deep male
AVAILABLE_VOICES: list[str] = [
    "en-US-GuyNeural",
    "en-US-JennyNeural",
    "en-GB-RyanNeural",
    "en-US-AriaNeural",
    "en-US-DavisNeural",
]

# ── Text/Telop Settings ───────────────────────────────────────
FONT_SIZE: int = 70
FONT_COLOR: str = "white"
STROKE_COLOR: str = "black"
STROKE_WIDTH: int = 3
AUTHOR_FONT_SIZE: int = 40

# ── History ────────────────────────────────────────────────────
HISTORY_FILE = HISTORY_DIR / "generated_history.json"

# ── Pexels Settings ────────────────────────────────────────────
PEXELS_FALLBACK_KEYWORDS: list[str] = [
    "nature landscape",
    "ocean waves",
    "sunset sky",
    "mountain clouds",
    "rain drops",
    "night city lights",
    "forest fog",
    "abstract light",
]

# ── Validation Limits ──────────────────────────────────────────
MAX_FILE_SIZE_MB: int = 50
MIN_SCENE_DURATION: float = 2.0
MAX_SCENE_DURATION: float = 8.0
