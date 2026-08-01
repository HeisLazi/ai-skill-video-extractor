"""Configuration management for AI Skill Video Extractor."""
import os
from dotenv import load_dotenv

load_dotenv()

# Versioning
SCHEMA_VERSION = "0.1"
PROMPT_VERSION = "video_extraction_v1"

# Defaults
DEFAULT_MODEL = "gemini-3.6-flash"
DEFAULT_OUTPUT_DIR = "./exports"

# Retry settings
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2

# Index
PROCESSED_INDEX_FILE = "processed-index.json"


def get_api_key(session_key: str | None = None) -> str | None:
    """Get API key with priority: session > environment."""
    if session_key and session_key.strip():
        return session_key.strip()
    env_key = os.getenv("GEMINI_API_KEY", "").strip()
    return env_key if env_key else None


def get_model(env_override: str | None = None) -> str:
    """Get model name from env or default."""
    if env_override and env_override.strip():
        return env_override.strip()
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


def mask_api_key(key: str) -> str:
    """Mask API key for display. Shows first 4 and last 4 chars."""
    if not key or len(key) < 10:
        return "****"
    return f"{key[:4]}...{key[-4:]}"
