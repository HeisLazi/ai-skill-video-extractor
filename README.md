# 🎬 AI Skill Video Extractor v0.1

A local utility that uses Google Gemini to analyze YouTube videos and extract structured knowledge for building an AI Agent Skills library.

## What This Does

1. You provide YouTube video or playlist URLs
2. Gemini analyzes **both spoken content and visual demonstrations**
3. Structured evidence files are generated locally
4. You give these files to GPT for deeper review and skill creation

> **Important:** Gemini's analysis produces **candidate knowledge** — evidence and observations, NOT canonical skill guidance. GPT/human review comes afterwards before anything becomes a permanent Agent Skill.

## Quick Start

### Prerequisites

- Python 3.11+
- A Google Gemini API key ([Get one here](https://aistudio.google.com/apikey))
- yt-dlp (installed via requirements.txt)

### Setup

```bash
# Clone or navigate to the project
cd ai-skill-video-extractor

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
copy .env.example .env  # Windows
# cp .env.example .env  # macOS/Linux

# Add your Gemini API key to .env
# Edit .env and set: GEMINI_API_KEY=your_key_here
```

### Run

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Usage

1. **Select input mode:** Single Video, Multiple Videos, or Playlist
2. **Paste URL(s)** into the input field
3. **Click "Discover Videos"** to enumerate and inspect what was found
4. **Select/deselect** individual videos as needed
5. **Click "Start Analysis"** to run Gemini analysis
6. **Monitor progress** — failures on individual videos won't kill the run
7. **Find results** in the `exports/` directory
8. **Give the export folder** (or `run-summary.md` + video folders) to GPT for review

## Configuration

### API Key

| Method | Priority | How |
|--------|----------|-----|
| Session input | 1 (highest) | Enter in sidebar password field |
| Environment | 2 | Set `GEMINI_API_KEY` in `.env` |

The API key is never displayed, logged, or written to output files.

### Model

Default: `gemini-3.6-flash`

Configurable via:
- `.env` file: `GEMINI_MODEL=gemini-3.6-flash`
- Sidebar text input in the UI

### Settings

| Setting | Default | Description |
|---------|---------|-------------|
| Output Directory | `./exports` | Where run folders are created |
| Skip Processed | ✅ On | Don't re-analyze videos already done |
| Retry Failed | ❌ Off | Re-attempt previously failed videos |
| Max Videos | 50 | Limit per run |

## Output Structure

```
exports/
  2025-01-15_my-playlist/
    README.md                  # Run description
    manifest.json              # All discovered videos + status
    run-summary.md             # Summary table for GPT review
    errors.jsonl               # Error log (if any)
    videos/
      001_great-design_dQw4w9/
        source.json            # Video metadata
        analysis.json          # Full structured Gemini analysis
        REVIEW.md              # Human/AI-readable review
      002_debugging-tips_xYz1/
        source.json
        analysis.json
        REVIEW.md
  processed-index.json         # Deduplication index
```

### Key Files

- **`run-summary.md`** — Start here. Give this to GPT first. Contains a table of all videos, categories, priorities, and cross-video theme aggregation.
- **`analysis.json`** — Complete structured analysis (JSON). Machine-readable.
- **`REVIEW.md`** — Human-readable version of the analysis.
- **`source.json`** — Video metadata only.
- **`manifest.json`** — Full run status tracking.

## What Gemini Extracts

For each video, Gemini analyzes both spoken content and visual demonstrations:

| Category | Description |
|----------|-------------|
| **Candidate Principles** | Principles the creator teaches (with confidence levels) |
| **Techniques** | Concrete, actionable techniques with steps |
| **Visual Observations** | Design changes visible on screen (spacing, color, hierarchy, etc.) |
| **Coding Observations** | Architecture, patterns, debugging approaches |
| **Workflows** | Step-by-step processes demonstrated |
| **Before/After Examples** | Modifications with original state, problem, change, result |
| **Anti-patterns** | Mistakes or bad practices warned against |
| **Agent Behaviors** | Specific behaviors an AI agent should adopt |
| **Skill Candidates** | Potential Agent Skills that could be created |
| **Uncertainties** | Things Gemini isn't sure about (mandatory section) |

Each observation includes confidence levels, evidence types (spoken/visual/both/inferred), and timestamps where available.

## Cost Control

- **One Gemini call per video** (no extra summarization calls)
- **Skip already-processed videos** by default
- **No cross-video Gemini synthesis** (done locally via aggregation)
- **No automatic re-runs** of successful videos
- API token usage is tracked and displayed when available

## Project Structure

```
ai-skill-video-extractor/
  app.py                 # Streamlit UI
  README.md
  requirements.txt
  .env.example
  .gitignore
  src/
    __init__.py
    config.py            # Configuration & API key handling
    schemas.py           # Pydantic models for structured output
    utils.py             # URL parsing, slugs, formatting
    youtube.py           # yt-dlp metadata extraction
    gemini_client.py     # Gemini API client with retries
    exporter.py          # File/directory management
    renderer.py          # Markdown rendering (no API calls)
    index.py             # Deduplication index
  prompts/
    video_extraction_v1.md  # The extraction prompt
  tests/
    test_video_id.py
    test_schemas.py
    test_exporter.py
    test_index.py
  exports/
    .gitkeep
```

## Tests

Run tests (no API key required):

```bash
python -m pytest tests/ -v
```

Tests cover URL parsing, schema validation, file exports, and index behavior without making any API calls.

## Versioning

- **Schema Version:** `0.1`
- **Prompt Version:** `video_extraction_v1`

Both are recorded in every analysis for tracking when extraction logic improves.

## Workflow: From Video to Skill

```
YouTube Video
  → Gemini Analysis (this tool)
    → Structured Evidence Files
      → GPT Review
        → Agent Skill (future phase)
```

This tool handles steps 1-3. Steps 4-5 are done separately.

## Known Limitations

- v0.1 processes one video per Gemini request
- No cross-video synthesis by Gemini (done locally via category counting)
- Playlist extraction requires yt-dlp to be working
- Private/unlisted videos may not be accessible to Gemini
- Very long videos may hit token limits on some models
- Visual analysis quality depends on video resolution and content type

## License

Personal utility — not intended for redistribution.
