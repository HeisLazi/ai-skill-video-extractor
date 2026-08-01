"""Export management: directories, source.json, analysis.json, manifest, errors."""
import json
import logging
from datetime import datetime
from pathlib import Path

from .schemas import (
    VideoAnalysis, VideoSource, ManifestEntry, RunManifest,
    ErrorRecord, VideoStatus,
)
from .utils import make_video_folder_name

logger = logging.getLogger(__name__)


def create_run_directory(base_dir: str, run_name: str | None = None) -> Path:
    """Create the run directory structure.
    
    Creates: exports/YYYY-MM-DD_run-name/
    """
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    if run_name:
        dir_name = f"{date_str}_{run_name}"
    else:
        dir_name = f"{date_str}_run"
    
    run_dir = base / dir_name
    
    # Handle duplicate run names by appending counter
    if run_dir.exists():
        counter = 2
        while (base / f"{dir_name}_{counter}").exists():
            counter += 1
        run_dir = base / f"{dir_name}_{counter}"
    
    run_dir.mkdir(parents=True)
    (run_dir / "videos").mkdir()
    
    return run_dir


def save_source_json(video_dir: Path, source: VideoSource) -> Path:
    """Save source.json to a video directory."""
    path = video_dir / "source.json"
    path.write_text(
        source.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return path


def save_analysis_json(video_dir: Path, analysis: VideoAnalysis) -> Path:
    """Save analysis.json to a video directory."""
    path = video_dir / "analysis.json"
    path.write_text(
        analysis.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return path


def save_manifest(run_dir: Path, manifest: RunManifest) -> Path:
    """Save manifest.json to the run directory."""
    path = run_dir / "manifest.json"
    path.write_text(
        manifest.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return path


def append_error(run_dir: Path, error: ErrorRecord) -> None:
    """Append an error record to errors.jsonl."""
    path = run_dir / "errors.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(error.model_dump_json() + "\n")


def create_video_directory(
    run_dir: Path,
    index: int,
    title: str | None,
    video_id: str,
) -> Path:
    """Create a numbered video subdirectory."""
    folder_name = make_video_folder_name(index, title, video_id)
    video_dir = run_dir / "videos" / folder_name
    video_dir.mkdir(parents=True, exist_ok=True)
    return video_dir


def save_readme(run_dir: Path, run_name: str, model: str, playlist_url: str | None = None) -> Path:
    """Create README.md for the run directory."""
    lines = [
        f"# Run: {run_name}",
        "",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Model:** {model}",
    ]
    if playlist_url:
        lines.append(f"**Playlist:** {playlist_url}")
    lines.extend([
        "",
        "## Contents",
        "",
        "- `manifest.json` — Full list of discovered/selected videos and their processing status",
        "- `run-summary.md` — Human/AI-readable summary of results",
        "- `errors.jsonl` — Log of processing errors (if any)",
        "- `videos/` — Individual video analysis directories",
        "",
        "## Usage",
        "",
        "Give this folder (or `run-summary.md` + individual video folders) to GPT for deeper review.",
        "",
        "## Important",
        "",
        "The analysis in this folder is **candidate knowledge** extracted by Gemini.",
        "It has NOT been reviewed or validated. GPT/human review comes next.",
    ])
    path = run_dir / "README.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
