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

# ── API Keys & Integrations ────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
PEXELS_API_KEY: str = os.getenv("PEXELS_API_KEY", "")
MAKE_WEBHOOK_URL: str = os.getenv("MAKE_WEBHOOK_URL", "https://hook.eu1.make.com/e2unkf0qe26uikpkqwabjtr6vil98731")
GITHUB_REPOSITORY: str = os.getenv("GITHUB_REPOSITORY", "trend9/tiktok-auto")  # Used for RAW URL construction

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

# ── Text/Telop Settings (Comic-book Style) ──────────────────────
FONT_SIZE: int = 85
STROKE_WIDTH: int = 5
AUTHOR_FONT_SIZE: int = 55
DROP_SHADOW_OFFSET: tuple[int, int] = (6, 6)

# Repertoire of telop colors (Font Color, Stroke Color, Shadow Color)
TELOP_PALETTES: list[dict[str, str]] = [
    {"font": "#FFE81F", "stroke": "black", "shadow": "black"}, # Bright comic yellow
    {"font": "#FFFFFF", "stroke": "black", "shadow": "black"}, # White
    {"font": "#00FF00", "stroke": "black", "shadow": "black"}, # Neon Green
    {"font": "#FF00FF", "stroke": "black", "shadow": "black"}, # Magenta
    {"font": "#00FFFF", "stroke": "black", "shadow": "black"}, # Cyan
    {"font": "#FF5555", "stroke": "black", "shadow": "black"}, # Light Red
    {"font": "#FFB6C1", "stroke": "black", "shadow": "black"}, # Light Pink
    {"font": "#FFA500", "stroke": "black", "shadow": "black"}, # Orange
    # Luxurious Palettes
    {"font": "#FFD700", "stroke": "#333333", "shadow": "black"}, # Gold
    {"font": "#F7E7CE", "stroke": "#333333", "shadow": "black"}, # Champagne
    {"font": "#E5E4E2", "stroke": "#222222", "shadow": "black"}, # Platinum
    {"font": "#B76E79", "stroke": "#222222", "shadow": "black"}, # Rose Gold
    {"font": "#FFFFFF", "stroke": "#D4AF37", "shadow": "black"}, # White with Gold Stroke
]

# ── Cinematic Grading & Audio Settings ───────────────────────────
TINT_COLOR: tuple[int, int, int] = (10, 25, 47)  # Dark Teal
TINT_OPACITY: float = 0.4
BGM_VOLUME: float = 0.08  # Lowered volume so it does not overpower TTS

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
