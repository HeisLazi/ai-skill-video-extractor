"""Tests for export functionality."""
import json
import tempfile
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.exporter import (
    create_run_directory, save_source_json, save_analysis_json,
    create_video_directory,
)
from src.schemas import VideoSource, VideoAnalysis
from src.utils import make_slug, make_video_folder_name


class TestMakeSlug:
    def test_simple(self):
        assert make_slug("Hello World") == "hello-world"

    def test_special_chars(self):
        assert make_slug("Hello! @World #2024") == "hello-world-2024"

    def test_unicode(self):
        slug = make_slug("Héllo Wörld")
        assert slug == "hello-world"

    def test_empty(self):
        assert make_slug("") == "untitled"

    def test_none(self):
        assert make_slug(None) == "untitled"

    def test_max_length(self):
        long_text = "a" * 100
        slug = make_slug(long_text, max_length=20)
        assert len(slug) <= 20

    def test_leading_trailing_hyphens(self):
        assert make_slug("---hello---") == "hello"


class TestMakeVideoFolderName:
    def test_basic(self):
        name = make_video_folder_name(1, "Great Video", "dQw4w9WgXcQ")
        assert name == "001_great-video_dQw4w9WgXcQ"

    def test_no_title(self):
        name = make_video_folder_name(1, None, "dQw4w9WgXcQ")
        assert name == "001_untitled_dQw4w9WgXcQ"

    def test_high_index(self):
        name = make_video_folder_name(42, "Test", "abc")
        assert name.startswith("042_")


class TestCreateRunDirectory:
    def test_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = create_run_directory(tmpdir, "test-run")
            assert run_dir.exists()
            assert (run_dir / "videos").exists()
            assert "test-run" in run_dir.name

    def test_handles_duplicate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dir1 = create_run_directory(tmpdir, "test")
            dir2 = create_run_directory(tmpdir, "test")
            assert dir1 != dir2
            assert dir2.exists()


class TestSaveFiles:
    def test_save_source(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from pathlib import Path
            video_dir = Path(tmpdir) / "test_video"
            video_dir.mkdir()
            source = VideoSource(
                video_id="test123",
                url="https://youtube.com/watch?v=test123",
                title="Test",
            )
            path = save_source_json(video_dir, source)
            assert path.exists()
            data = json.loads(path.read_text())
            assert data["video_id"] == "test123"

    def test_save_analysis(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from pathlib import Path
            video_dir = Path(tmpdir) / "test_video"
            video_dir.mkdir()
            analysis = VideoAnalysis(
                title="Test",
                summary="A test.",
            )
            path = save_analysis_json(video_dir, analysis)
            assert path.exists()
            data = json.loads(path.read_text())
            assert data["title"] == "Test"
