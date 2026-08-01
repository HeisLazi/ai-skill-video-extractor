"""Gemini API client for structured video analysis."""
import json
import time
import logging
from pathlib import Path
from dataclasses import dataclass, field

from google import genai
from google.genai import types

from .config import MAX_RETRIES, RETRY_BACKOFF_BASE, PROMPT_VERSION
from .schemas import VideoAnalysis

logger = logging.getLogger(__name__)

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "video_extraction_v1.md"


@dataclass
class AnalysisResult:
    """Result of a video analysis attempt."""
    success: bool
    analysis: VideoAnalysis | None = None
    error: str | None = None
    error_type: str | None = None
    retryable: bool = False
    attempts: int = 0
    usage_metadata: dict | None = None


@dataclass
class APIStats:
    """Simple API usage counters."""
    requests_attempted: int = 0
    requests_successful: int = 0
    requests_failed: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0


def load_extraction_prompt() -> str:
    """Load the extraction prompt from the prompts directory."""
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(
            f"Extraction prompt not found at {PROMPT_FILE}. "
            "Ensure prompts/video_extraction_v1.md exists."
        )
    return PROMPT_FILE.read_text(encoding="utf-8")


def _is_retryable_error(error: Exception) -> bool:
    """Determine if an error is transient and worth retrying."""
    error_str = str(error).lower()
    retryable_indicators = [
        "rate limit", "quota", "429", "500", "503", "unavailable",
        "deadline", "timeout", "internal", "temporarily",
        "resource_exhausted", "overloaded",
    ]
    return any(indicator in error_str for indicator in retryable_indicators)


def _is_permanent_error(error: Exception) -> bool:
    """Determine if an error should not be retried."""
    error_str = str(error).lower()
    permanent_indicators = [
        "invalid", "not found", "permission", "forbidden", "401", "403",
        "private", "unavailable video", "blocked", "safety",
    ]
    return any(indicator in error_str for indicator in permanent_indicators)


def analyze_video(
    api_key: str,
    video_url: str,
    model: str,
    stats: APIStats | None = None,
) -> AnalysisResult:
    """Analyze a single YouTube video using Gemini.
    
    Args:
        api_key: Gemini API key
        video_url: YouTube video URL
        model: Model name to use
        stats: Optional stats tracker
    
    Returns:
        AnalysisResult with success/failure and data
    """
    if stats is None:
        stats = APIStats()
    
    extraction_prompt = load_extraction_prompt()
    
    client = genai.Client(api_key=api_key)
    
    attempts = 0
    last_error = None
    
    while attempts < MAX_RETRIES:
        attempts += 1
        stats.requests_attempted += 1
        
        try:
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_uri(
                                file_uri=video_url,
                                mime_type="video/youtube",
                            ),
                            types.Part.from_text(text=extraction_prompt),
                        ],
                    )
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=VideoAnalysis,
                    temperature=0.2,
                ),
            )
            
            # Extract usage metadata if available
            usage_meta = None
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                um = response.usage_metadata
                usage_meta = {
                    "input_tokens": getattr(um, 'prompt_token_count', None) or getattr(um, 'input_tokens', None),
                    "output_tokens": getattr(um, 'candidates_token_count', None) or getattr(um, 'output_tokens', None),
                    "total_tokens": getattr(um, 'total_token_count', None) or getattr(um, 'total_tokens', None),
                }
                if usage_meta.get("input_tokens"):
                    stats.total_input_tokens += usage_meta["input_tokens"]
                if usage_meta.get("output_tokens"):
                    stats.total_output_tokens += usage_meta["output_tokens"]
            
            # Try to get parsed response first, fall back to manual parsing
            analysis = None
            if hasattr(response, 'parsed') and response.parsed is not None:
                analysis = response.parsed
            else:
                # Manual parse from text
                raw_text = response.text
                if raw_text:
                    analysis = VideoAnalysis.model_validate_json(raw_text)
            
            if analysis is None:
                raise ValueError("Empty response from Gemini")
            
            # Stamp versions
            analysis.schema_version = "0.1"
            analysis.prompt_version = PROMPT_VERSION
            
            stats.requests_successful += 1
            
            return AnalysisResult(
                success=True,
                analysis=analysis,
                attempts=attempts,
                usage_metadata=usage_meta,
            )
        
        except Exception as e:
            last_error = e
            error_str = str(e)
            
            # Sanitize error message (remove potential key leaks)
            sanitized = error_str
            if api_key and len(api_key) > 8:
                sanitized = sanitized.replace(api_key, "[REDACTED]")
            
            logger.warning(
                f"Gemini analysis attempt {attempts}/{MAX_RETRIES} failed: {sanitized}"
            )
            
            if _is_permanent_error(e):
                stats.requests_failed += 1
                return AnalysisResult(
                    success=False,
                    error=sanitized,
                    error_type=type(e).__name__,
                    retryable=False,
                    attempts=attempts,
                )
            
            if _is_retryable_error(e) and attempts < MAX_RETRIES:
                backoff = RETRY_BACKOFF_BASE ** attempts
                logger.info(f"Retrying in {backoff}s...")
                time.sleep(backoff)
                continue
            
            # Validation error: try one more parse attempt
            if attempts == 1 and "validation" in error_str.lower():
                continue
    
    stats.requests_failed += 1
    sanitized_error = str(last_error) if last_error else "Unknown error"
    if api_key and len(api_key) > 8:
        sanitized_error = sanitized_error.replace(api_key, "[REDACTED]")
    
    return AnalysisResult(
        success=False,
        error=sanitized_error,
        error_type=type(last_error).__name__ if last_error else "Unknown",
        retryable=_is_retryable_error(last_error) if last_error else False,
        attempts=attempts,
    )
