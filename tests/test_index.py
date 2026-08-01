"""Tests for processed index behavior."""
import tempfile
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.index import (
    load_index, save_index, is_already_processed,
    mark_processed, remove_from_index,
)
from src.schemas import ProcessedIndex


class TestProcessedIndex:
    def test_load_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            index = load_index(tmpdir)
            assert index.entries == {}

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            index = ProcessedIndex()
            mark_processed(index, "abc123", "gemini-3.6-flash", "/path/to/output", "0.1")
            save_index(tmpdir, index)

            loaded = load_index(tmpdir)
            assert "abc123" in loaded.entries
            assert loaded.entries["abc123"].model == "gemini-3.6-flash"

    def test_is_already_processed(self):
        index = ProcessedIndex()
        mark_processed(index, "abc123", "gemini-3.6-flash", "/path", "0.1")

        assert is_already_processed(index, "abc123", "0.1") is True
        assert is_already_processed(index, "abc123", "0.2") is False
        assert is_already_processed(index, "xyz789", "0.1") is False

    def test_remove_from_index(self):
        index = ProcessedIndex()
        mark_processed(index, "abc123", "gemini-3.6-flash", "/path", "0.1")

        assert remove_from_index(index, "abc123") is True
        assert remove_from_index(index, "abc123") is False
        assert is_already_processed(index, "abc123") is False

    def test_mark_overwrites(self):
        index = ProcessedIndex()
        mark_processed(index, "abc123", "model-1", "/path1", "0.1")
        mark_processed(index, "abc123", "model-2", "/path2", "0.1")

        assert index.entries["abc123"].model == "model-2"
        assert index.entries["abc123"].output_folder == "/path2"
