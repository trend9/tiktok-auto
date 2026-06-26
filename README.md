# 🎬 TikTok Auto Video Generator

Automatically generate motivational quote short videos (9:16, <60s) for TikTok — powered entirely by **free APIs**.

## ✨ Features

- **AI-powered content** — Gemini API generates unique themes & quotes every time
- **Text-to-Speech** — Edge-TTS produces natural English narration
- **Stock video backgrounds** — Pexels API provides cinematic backdrops
- **Duplicate prevention** — JSON history ensures no theme is ever repeated
- **3-stage validation** — Scenario → Assets → Output verified before finalizing
- **GitHub Actions ready** — Fully automated with scheduled daily runs
- **60 videos/month** — All within free API limits

## 🏗️ Architecture

```
Theme (Gemini) → Scenario (Gemini) → Validate
    → TTS Audio (Edge-TTS) + Background Video (Pexels)
    → Validate → Compose (MoviePy) → Validate → Output MP4
```

## 📋 Prerequisites

- Python 3.10+
- FFmpeg (for video encoding)
- API Keys (all free):
  - [Google Gemini API](https://aistudio.google.com/) — for AI content generation
  - [Pexels API](https://www.pexels.com/api/) — for stock video backgrounds

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd tiktok-auto
pip install -r requirements.txt
```

### 2. Set up API keys

```bash
cp .env.example .env
# Edit .env and add your API keys
```

### 3. Install FFmpeg

**Windows:**
```bash
winget install FFmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

### 4. Generate a video

```bash
# Generate 1 video
python main.py --count 1

# Generate 5 videos
python main.py --count 5

# Use a different voice
python main.py --voice en-US-JennyNeural
```

## 🤖 GitHub Actions (Automated)

### Setup

1. Push this repo to GitHub
2. Go to **Settings → Secrets and variables → Actions**
3. Add these secrets:
   - `GEMINI_API_KEY` — your Gemini API key
   - `PEXELS_API_KEY` — your Pexels API key
4. The workflow runs daily and generates 2 videos per run

### Manual trigger

Go to **Actions → Generate TikTok Videos → Run workflow** and specify the count.

### Download videos

Generated videos are uploaded as **Artifacts** on each workflow run. Download them from the Actions tab.

## 📁 Project Structure

```
tiktok-auto/
├── .github/workflows/     # GitHub Actions
├── generators/            # Theme & scenario generation (Gemini)
├── tts/                   # Text-to-Speech (Edge-TTS)
├── media/                 # Background video download (Pexels)
├── video/                 # Video composition & validation
├── history/               # Generation history (duplicate prevention)
├── output/                # Final MP4 files
├── config.py              # All configuration
└── main.py                # Entry point
```

## 🎤 Available Voices

| Voice | Description |
|:------|:------------|
| `en-US-GuyNeural` | Calm American male (default) |
| `en-US-JennyNeural` | Clear American female |
| `en-GB-RyanNeural` | British male |
| `en-US-AriaNeural` | Expressive American female |
| `en-US-DavisNeural` | Deep American male |

## 📊 API Usage (Monthly)

| API | Per Video | 60 Videos/Month | Free Limit | Status |
|:----|:----------|:-----------------|:-----------|:-------|
| Gemini | ~3 req | ~180 req | 1500 RPD | ✅ |
| Pexels | ~3 req | ~180 req | 20,000/month | ✅ |
| Edge-TTS | ~10 req | ~600 req | Unlimited | ✅ |
| GitHub Actions | ~5 min | ~300 min | 2,000 min/month | ✅ |

## 📄 License

MIT
