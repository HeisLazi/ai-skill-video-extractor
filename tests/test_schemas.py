"""Tests for Pydantic schema validation."""
import json
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.schemas import (
    VideoAnalysis, VideoSource, CandidatePrinciple, Technique,
    VisualObservation, CodingObservation, Workflow, WorkflowStep,
    BeforeAfterExample, AntiPattern, CandidateAgentBehavior,
    SkillCandidate, Uncertainty, ManifestEntry, RunManifest,
    ProcessedIndex, ProcessedEntry, ErrorRecord,
    ConfidenceLevel, EvidenceType, ReviewPriority, SkillDisposition, VideoStatus,
)


def make_minimal_analysis() -> dict:
    """Create minimal valid analysis data."""
    return {
        "title": "Test Video",
        "summary": "A test video about testing.",
        "uncertainties": [
            {
                "topic": "Test uncertainty",
                "details": "This is uncertain.",
                "category": "needs_verification",
            }
        ],
    }


def make_full_analysis() -> dict:
    """Create a fully-populated analysis for testing."""
    return {
        "schema_version": "0.1",
        "prompt_version": "video_extraction_v1",
        "title": "Dashboard Design Masterclass",
        "summary": "A deep dive into dashboard design principles.",
        "thesis": "Good dashboards prioritize information hierarchy.",
        "audience": "Frontend developers and UI designers",
        "topics": ["dashboard design", "visual hierarchy", "data visualization"],
        "tools_shown": ["Figma", "React", "Tailwind CSS"],
        "candidate_principles": [
            {
                "name": "Information Hierarchy First",
                "explanation": "Establish what is primary, secondary, tertiary before styling.",
                "why_it_matters": "Prevents equal-prominence anti-pattern.",
                "context": "Dashboard and data-heavy UI design",
                "does_not_apply_when": "Very simple single-metric displays",
                "timestamp": "3:45-5:20",
                "confidence": "high",
                "evidence_type": "both",
            }
        ],
        "techniques": [
            {
                "name": "Progressive Disclosure",
                "description": "Show summary first, details on demand.",
                "steps": ["Identify key metrics", "Design summary view", "Add drill-down"],
                "intended_result": "Reduced cognitive load",
                "prerequisites": ["Understanding of user workflows"],
                "tools_involved": ["Figma"],
                "timestamp": "7:00",
                "reusable_by_ai_agent": True,
                "confidence": "high",
            }
        ],
        "visual_observations": [
            {
                "what_changed": "Card spacing increased from tight to generous",
                "before": "Cards touching with 4px gap",
                "after": "Cards with 16px gap and subtle shadow",
                "likely_reason": "Improve scannability",
                "observed_effect": "Dashboard feels less cluttered",
                "timestamp": "10:30",
                "confidence": "high",
            }
        ],
        "coding_observations": [
            {
                "category": "architecture",
                "observation": "Component composition over inheritance",
                "details": "Used render props pattern for flexible chart layouts.",
                "explicitly_recommended": True,
                "timestamp": "15:00",
                "confidence": "high",
            }
        ],
        "workflows": [
            {
                "name": "Dashboard Design Process",
                "purpose": "Systematic approach to dashboard design",
                "trigger": "Starting a new dashboard project",
                "steps": [
                    {"step_number": 1, "action": "Identify key metrics", "details": "Interview stakeholders"},
                    {"step_number": 2, "action": "Establish hierarchy", "details": None},
                    {"step_number": 3, "action": "Wireframe layout", "details": None},
                ],
                "exit_condition": "All metrics have clear visual weight",
                "mistakes_to_avoid": ["Starting with colors", "Equal prominence"],
                "timestamp": "2:00-20:00",
                "confidence": "high",
            }
        ],
        "before_after_examples": [
            {
                "original_state": "All cards same size and color",
                "identified_problem": "No visual hierarchy",
                "modification": "Primary metric enlarged, secondary reduced",
                "result": "Clear focal point established",
                "principle_demonstrated": "Information Hierarchy",
                "timestamp": "12:00",
            }
        ],
        "anti_patterns": [
            {
                "name": "Equal Prominence",
                "why_problematic": "When everything is important, nothing is.",
                "better_alternative": "Assign visual weight based on importance.",
                "context": "Dashboard design",
                "timestamp": "5:30",
                "confidence": "high",
            }
        ],
        "candidate_agent_behaviors": [
            {
                "behavior": "Prioritize information hierarchy in dashboards",
                "trigger": "Building a dashboard or data-heavy UI",
                "action": "Before styling, classify all elements as primary/secondary/tertiary",
                "expected_outcome": "Clear visual hierarchy with appropriate emphasis",
                "supporting_evidence": "Creator demonstrates this at 3:45",
                "confidence": "high",
            }
        ],
        "candidate_skill_categories": ["visual-hierarchy", "dashboard-design", "layout"],
        "skill_candidates": [
            {
                "skill_name": "dashboard-hierarchy-design",
                "description": "Apply information hierarchy to dashboard layouts.",
                "evidence_from_video": "Full workflow demonstrated with before/after.",
                "possible_triggers": ["dashboard", "data visualization", "metrics display"],
                "what_skill_would_teach": "How to establish visual hierarchy in dashboards.",
                "disposition": "create_new",
            }
        ],
        "uncertainties": [
            {
                "topic": "Specific spacing values",
                "details": "Exact pixel values for card gaps were not explicitly stated.",
                "category": "ambiguous_visual",
            }
        ],
        "review_priority": "high",
        "review_notes": "Strong before/after examples. Worth deep review.",
    }


class TestVideoAnalysis:
    def test_minimal_valid(self):
        data = make_minimal_analysis()
        analysis = VideoAnalysis.model_validate(data)
        assert analysis.title == "Test Video"
        assert analysis.schema_version == "0.1"
        assert len(analysis.uncertainties) == 1

    def test_full_valid(self):
        data = make_full_analysis()
        analysis = VideoAnalysis.model_validate(data)
        assert analysis.title == "Dashboard Design Masterclass"
        assert len(analysis.candidate_principles) == 1
        assert len(analysis.techniques) == 1
        assert len(analysis.visual_observations) == 1
        assert analysis.review_priority == ReviewPriority.high

    def test_json_roundtrip(self):
        data = make_full_analysis()
        analysis = VideoAnalysis.model_validate(data)
        json_str = analysis.model_dump_json(indent=2)
        restored = VideoAnalysis.model_validate_json(json_str)
        assert restored.title == analysis.title
        assert len(restored.candidate_principles) == len(analysis.candidate_principles)

    def test_defaults(self):
        analysis = VideoAnalysis(
            title="Test",
            summary="Test summary",
        )
        assert analysis.schema_version == "0.1"
        assert analysis.candidate_principles == []
        assert analysis.techniques == []
        assert analysis.review_priority == ReviewPriority.medium

    def test_invalid_confidence(self):
        data = make_minimal_analysis()
        data["candidate_principles"] = [{
            "name": "Test",
            "explanation": "Test",
            "why_it_matters": "Test",
            "context": "Test",
            "confidence": "invalid_value",
            "evidence_type": "spoken",
        }]
        with pytest.raises(Exception):
            VideoAnalysis.model_validate(data)


class TestVideoSource:
    def test_basic(self):
        source = VideoSource(
            video_id="dQw4w9WgXcQ",
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            title="Test Video",
        )
        assert source.video_id == "dQw4w9WgXcQ"
        assert source.schema_version == "0.1"
        assert source.retrieved_at is not None


class TestManifest:
    def test_manifest_creation(self):
        manifest = RunManifest(
            run_name="test-run",
            model="gemini-3.6-flash",
        )
        assert manifest.run_name == "test-run"
        assert manifest.videos == []

    def test_manifest_entry(self):
        entry = ManifestEntry(
            video_id="abc123",
            url="https://www.youtube.com/watch?v=abc123",
            status=VideoStatus.success,
        )
        assert entry.status == VideoStatus.success


class TestProcessedIndex:
    def test_empty_index(self):
        index = ProcessedIndex()
        assert index.entries == {}

    def test_add_entry(self):
        index = ProcessedIndex()
        index.entries["abc123"] = ProcessedEntry(
            video_id="abc123",
            last_processed="2025-01-01T00:00:00",
            model="gemini-3.6-flash",
            output_folder="001_test_abc123",
            schema_version="0.1",
        )
        assert "abc123" in index.entries


class TestErrorRecord:
    def test_error_record(self):
        error = ErrorRecord(
            video_url="https://youtube.com/watch?v=test",
            video_id="test",
            error_type="ValueError",
            error_message="Something went wrong",
            retryable=True,
        )
        assert error.retryable is True
        assert error.timestamp is not None
