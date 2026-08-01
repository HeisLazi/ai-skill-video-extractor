"""Unit tests for Gemini client (mocked, no API quota spent)."""
import json
import pytest
from unittest.mock import MagicMock, patch

from src.gemini_client import (
    analyze_video,
    load_extraction_prompt,
    APIStats,
    _is_retryable_error,
    _is_permanent_error,
)
from src.schemas import VideoAnalysis, ReviewPriority
from google.genai import types


def _sample_analysis() -> VideoAnalysis:
    return VideoAnalysis(
        title="Testing Video",
        summary="Summary of test video.",
        review_priority=ReviewPriority.high,
    )


class TestGeminiClientLogic:
    def test_load_extraction_prompt(self):
        prompt = load_extraction_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 50
        assert "candidate_principles" in prompt or "Candidate Principles" in prompt or "Visual Observations" in prompt

    def test_error_classification(self):
        assert _is_retryable_error(Exception("429 Resource Exhausted")) is True
        assert _is_retryable_error(Exception("Deadline exceeded")) is True
        assert _is_retryable_error(Exception("Connection timeout")) is True
        assert _is_retryable_error(Exception("Random syntax error")) is False

        assert _is_permanent_error(Exception("403 Forbidden")) is True
        assert _is_permanent_error(Exception("Private video")) is True
        assert _is_permanent_error(Exception("Safety block triggered")) is True
        assert _is_permanent_error(Exception("503 Service Unavailable")) is False


class TestMockedAnalyzeVideo:
    @patch("src.gemini_client.genai.Client")
    def test_analyze_video_success_with_parsed(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.parsed = _sample_analysis()
        mock_response.usage_metadata = MagicMock()
        mock_response.usage_metadata.prompt_token_count = 1200
        mock_response.usage_metadata.candidates_token_count = 450
        mock_response.usage_metadata.total_token_count = 1650

        mock_client.models.generate_content.return_value = mock_response

        stats = APIStats()
        result = analyze_video(
            api_key="test_fake_api_key_12345",
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            model="gemini-3.6-flash",
            stats=stats,
        )

        assert result.success is True
        assert result.analysis is not None
        assert result.analysis.title == "Testing Video"
        assert result.analysis.schema_version == "0.1"
        assert result.analysis.prompt_version == "video_extraction_v1"
        assert stats.requests_successful == 1
        assert stats.total_input_tokens == 1200
        assert stats.total_output_tokens == 450

        # Verify call arguments to generate_content
        mock_client.models.generate_content.assert_called_once()
        call_kwargs = mock_client.models.generate_content.call_args.kwargs
        assert call_kwargs["model"] == "gemini-3.6-flash"

        # Verify contents: should have types.Part with FileData
        contents = call_kwargs["contents"]
        content_item = contents[0]
        parts = content_item.parts
        video_part = parts[0]
        assert isinstance(video_part, types.Part)
        assert video_part.file_data is not None
        assert video_part.file_data.file_uri == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

        # Verify config: no temperature, response_schema present
        config = call_kwargs["config"]
        assert config.response_mime_type == "application/json"
        assert config.response_schema == VideoAnalysis
        assert getattr(config, "temperature", None) is None

    @patch("src.gemini_client.genai.Client")
    def test_analyze_video_fallback_to_json_text(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.parsed = None
        mock_response.text = json.dumps({
            "title": "Parsed from text",
            "summary": "Fallback parsing works.",
            "review_priority": "medium",
        })
        mock_response.usage_metadata = None

        mock_client.models.generate_content.return_value = mock_response

        result = analyze_video(
            api_key="test_fake_api_key_12345",
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            model="gemini-3.6-flash",
        )

        assert result.success is True
        assert result.analysis is not None
        assert result.analysis.title == "Parsed from text"

    @patch("src.gemini_client.genai.Client")
    def test_analyze_video_permanent_failure_no_retry(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("403 Forbidden: private video")

        stats = APIStats()
        result = analyze_video(
            api_key="secret_key_12345678",
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            model="gemini-3.6-flash",
            stats=stats,
        )

        assert result.success is False
        assert result.retryable is False
        assert result.attempts == 1
        assert stats.requests_failed == 1
        assert "secret_key_12345678" not in result.error
        assert "[REDACTED]" in result.error or "secret_key" not in result.error

    @patch("src.gemini_client.time.sleep")
    @patch("src.gemini_client.genai.Client")
    def test_analyze_video_transient_failure_retried(self, mock_client_cls, mock_sleep):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("429 Resource Exhausted: rate limit")

        result = analyze_video(
            api_key="test_fake_key_12345678",
            video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            model="gemini-3.6-flash",
        )

        assert result.success is False
        assert result.retryable is True
        assert result.attempts == 3
        assert mock_sleep.call_count == 2
