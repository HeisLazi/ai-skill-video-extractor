"""Processed video index for deduplication."""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from .config import SCHEMA_VERSION, PROCESSED_INDEX_FILE
from .schemas import ProcessedIndex, ProcessedEntry

logger = logging.getLogger(__name__)


def get_index_path(exports_dir: str) -> Path:
    """Get the path to the processed index file."""
    return Path(exports_dir) / PROCESSED_INDEX_FILE


def load_index(exports_dir: str) -> ProcessedIndex:
    """Load the processed index, creating it if it doesn't exist."""
    path = get_index_path(exports_dir)
    if not path.exists():
        return ProcessedIndex()
    
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return ProcessedIndex.model_validate(data)
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Could not load processed index: {e}. Starting fresh.")
        return ProcessedIndex()


def save_index(exports_dir: str, index: ProcessedIndex) -> None:
    """Save the processed index."""
    path = get_index_path(exports_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        index.model_dump_json(indent=2),
        encoding="utf-8",
    )


def is_already_processed(
    index: ProcessedIndex,
    video_id: str,
    schema_version: str = SCHEMA_VERSION,
) -> bool:
    """Check if a video has already been successfully processed under the current schema."""
    if video_id not in index.entries:
        return False
    entry = index.entries[video_id]
    return entry.schema_version == schema_version


def mark_processed(
    index: ProcessedIndex,
    video_id: str,
    model: str,
    output_folder: str,
    schema_version: str = SCHEMA_VERSION,
) -> None:
    """Mark a video as successfully processed."""
    index.entries[video_id] = ProcessedEntry(
        video_id=video_id,
        last_processed=datetime.now(timezone.utc).isoformat(),
        model=model,
        output_folder=output_folder,
        schema_version=schema_version,
    )


def remove_from_index(index: ProcessedIndex, video_id: str) -> bool:
    """Remove a video from the index (for manual reprocessing). Returns True if found."""
    if video_id in index.entries:
        del index.entries[video_id]
        return True
    return False
