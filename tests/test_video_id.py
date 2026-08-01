"""Tests for YouTube video ID extraction."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils import extract_video_id, is_valid_youtube_url, is_playlist_url


class TestExtractVideoId:
    def test_standard_url(self):
        assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_short_url(self):
        assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_embed_url(self):
        assert extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_v_url(self):
        assert extract_video_id("https://www.youtube.com/v/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_shorts_url(self):
        assert extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_url_with_params(self):
        assert extract_video_id(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLtest&index=3"
        ) == "dQw4w9WgXcQ"

    def test_url_with_timestamp(self):
        assert extract_video_id(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120"
        ) == "dQw4w9WgXcQ"

    def test_invalid_url(self):
        assert extract_video_id("https://example.com") is None

    def test_empty_string(self):
        assert extract_video_id("") is None

    def test_none(self):
        assert extract_video_id(None) is None

    def test_whitespace(self):
        assert extract_video_id("  https://youtu.be/dQw4w9WgXcQ  ") == "dQw4w9WgXcQ"

    def test_no_protocol(self):
        # Should still match the domain pattern
        assert extract_video_id("youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


class TestIsValidYoutubeUrl:
    def test_valid(self):
        assert is_valid_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True

    def test_invalid(self):
        assert is_valid_youtube_url("https://example.com") is False


class TestIsPlaylistUrl:
    def test_playlist(self):
        assert is_playlist_url(
            "https://www.youtube.com/playlist?list=PLtest123"
        ) is True

    def test_not_playlist(self):
        assert is_playlist_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is False

    def test_empty(self):
        assert is_playlist_url("") is False

    def test_none(self):
        assert is_playlist_url(None) is False

    def test_video_with_list(self):
        assert is_playlist_url(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLtest"
        ) is True
