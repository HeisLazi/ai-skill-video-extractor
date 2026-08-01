"""Pydantic schemas for structured video analysis output."""
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class EvidenceType(str, Enum):
    spoken = "spoken"
    visual = "visual"
    both = "both"
    inferred = "inferred"


class ReviewPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class SkillDisposition(str, Enum):
    create_new = "create_new"
    update_existing = "update_existing"
    research_only = "research_only"


class VideoStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    success = "success"
    failed = "failed"
    skipped = "skipped"


# --- Sub-models for analysis ---

class CandidatePrinciple(BaseModel):
    """A principle the creator appears to teach."""
    name: str = Field(description="Short name for the principle")
    explanation: str = Field(description="What this principle means")
    why_it_matters: str = Field(description="Why this principle is important")
    context: str = Field(description="Context or domain where this applies")
    does_not_apply_when: Optional[str] = Field(default=None, description="Situations where this principle may NOT apply")
    timestamp: Optional[str] = Field(default=None, description="Timestamp or range in video (e.g., '2:30', '5:00-7:15')")
    confidence: ConfidenceLevel = Field(description="Confidence in this extraction")
    evidence_type: EvidenceType = Field(description="How this was observed")


class Technique(BaseModel):
    """A concrete technique demonstrated in the video."""
    name: str = Field(description="Short name for the technique")
    description: str = Field(description="What the creator did")
    steps: list[str] = Field(default_factory=list, description="Ordered steps of the technique")
    intended_result: Optional[str] = Field(default=None, description="What this technique achieves")
    prerequisites: list[str] = Field(default_factory=list, description="Required knowledge or tools")
    tools_involved: list[str] = Field(default_factory=list, description="Tools or frameworks used")
    timestamp: Optional[str] = Field(default=None, description="Timestamp in video")
    reusable_by_ai_agent: bool = Field(default=False, description="Whether an AI coding/design agent could use this")
    confidence: ConfidenceLevel = Field(description="Confidence in this extraction")


class VisualObservation(BaseModel):
    """A visual change or design decision observed in the video."""
    what_changed: str = Field(description="Description of the visual change")
    before: Optional[str] = Field(default=None, description="State before the change")
    after: Optional[str] = Field(default=None, description="State after the change")
    likely_reason: Optional[str] = Field(default=None, description="Why this change was likely made")
    observed_effect: Optional[str] = Field(default=None, description="The visual/UX effect of the change")
    timestamp: Optional[str] = Field(default=None, description="Timestamp in video")
    confidence: ConfidenceLevel = Field(description="Confidence in this observation")


class CodingObservation(BaseModel):
    """A coding practice, pattern, or decision observed."""
    category: str = Field(description="Category: architecture, pattern, abstraction, debugging, testing, refactoring, etc.")
    observation: str = Field(description="What was observed")
    details: Optional[str] = Field(default=None, description="Additional details or context")
    explicitly_recommended: bool = Field(default=False, description="True if the creator explicitly recommends this, False if inferred")
    timestamp: Optional[str] = Field(default=None, description="Timestamp in video")
    confidence: ConfidenceLevel = Field(description="Confidence in this observation")


class WorkflowStep(BaseModel):
    """A single step in a workflow."""
    step_number: int = Field(description="Order in the workflow")
    action: str = Field(description="What happens at this step")
    details: Optional[str] = Field(default=None, description="Additional context")


class Workflow(BaseModel):
    """A process or workflow demonstrated in the video."""
    name: str = Field(description="Name of the workflow")
    purpose: str = Field(description="What this workflow accomplishes")
    trigger: Optional[str] = Field(default=None, description="When to use this workflow")
    steps: list[WorkflowStep] = Field(default_factory=list, description="Ordered steps")
    exit_condition: Optional[str] = Field(default=None, description="How you know the workflow is complete")
    mistakes_to_avoid: list[str] = Field(default_factory=list, description="Common mistakes")
    timestamp: Optional[str] = Field(default=None, description="Timestamp evidence")
    confidence: ConfidenceLevel = Field(description="Confidence in this extraction")


class BeforeAfterExample(BaseModel):
    """A before/after modification demonstrated in the video."""
    original_state: str = Field(description="What it looked like before")
    identified_problem: str = Field(description="What problem was identified")
    modification: str = Field(description="What was changed")
    result: str = Field(description="What it looked like after")
    principle_demonstrated: Optional[str] = Field(default=None, description="What principle this demonstrates")
    timestamp: Optional[str] = Field(default=None, description="Timestamp in video")


class AntiPattern(BaseModel):
    """A mistake or bad practice warned against."""
    name: str = Field(description="Name of the anti-pattern")
    why_problematic: str = Field(description="Why this is a problem")
    better_alternative: Optional[str] = Field(default=None, description="What to do instead")
    context: Optional[str] = Field(default=None, description="When this applies")
    timestamp: Optional[str] = Field(default=None, description="Timestamp in video")
    confidence: ConfidenceLevel = Field(description="Confidence in this extraction")


class CandidateAgentBehavior(BaseModel):
    """A specific behavior an AI agent should adopt."""
    behavior: str = Field(description="Description of the behavior")
    trigger: str = Field(description="When the agent should activate this behavior")
    action: str = Field(description="What the agent should do")
    expected_outcome: str = Field(description="What should result")
    supporting_evidence: Optional[str] = Field(default=None, description="Evidence from the video")
    confidence: ConfidenceLevel = Field(description="Confidence in this candidate")


class SkillCandidate(BaseModel):
    """A potential Agent Skill identified from the video."""
    skill_name: str = Field(description="Proposed name for the skill")
    description: str = Field(description="What this skill would do")
    evidence_from_video: str = Field(description="What in the video supports this")
    possible_triggers: list[str] = Field(default_factory=list, description="When this skill would activate")
    what_skill_would_teach: str = Field(description="What knowledge the skill encodes")
    disposition: SkillDisposition = Field(description="Whether to create new, update existing, or keep as research")


class Uncertainty(BaseModel):
    """Something Gemini is uncertain about."""
    topic: str = Field(description="What the uncertainty is about")
    details: str = Field(description="Nature of the uncertainty")
    category: str = Field(description="Type: ambiguous_visual, unsupported_assumption, unclear_intent, outdated_practice, needs_verification, conflicting_advice, insufficient_evidence")


# --- Main analysis model ---

class VideoSource(BaseModel):
    """Source metadata for a video."""
    video_id: str
    url: str
    title: Optional[str] = None
    channel: Optional[str] = None
    playlist_name: Optional[str] = None
    playlist_url: Optional[str] = None
    playlist_index: Optional[int] = None
    duration_seconds: Optional[int] = None
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    analysis_model: Optional[str] = None
    schema_version: str = "0.1"


class VideoAnalysis(BaseModel):
    """Complete structured analysis of a YouTube video."""
    schema_version: str = Field(default="0.1", description="Schema version")
    prompt_version: str = Field(default="video_extraction_v1", description="Prompt version used")
    
    # Basic understanding
    title: str = Field(description="Video title or inferred topic")
    summary: str = Field(description="Concise summary of the video")
    thesis: Optional[str] = Field(default=None, description="Main thesis or argument")
    audience: Optional[str] = Field(default=None, description="Intended audience")
    topics: list[str] = Field(default_factory=list, description="Topics covered")
    tools_shown: list[str] = Field(default_factory=list, description="Tools, frameworks, or products shown")

    # Extracted knowledge
    candidate_principles: list[CandidatePrinciple] = Field(default_factory=list)
    techniques: list[Technique] = Field(default_factory=list)
    visual_observations: list[VisualObservation] = Field(default_factory=list)
    coding_observations: list[CodingObservation] = Field(default_factory=list)
    workflows: list[Workflow] = Field(default_factory=list)
    before_after_examples: list[BeforeAfterExample] = Field(default_factory=list)
    anti_patterns: list[AntiPattern] = Field(default_factory=list)

    # Agent-oriented
    candidate_agent_behaviors: list[CandidateAgentBehavior] = Field(default_factory=list)
    candidate_skill_categories: list[str] = Field(default_factory=list, description="Categories like visual-hierarchy, spacing, typography, etc.")
    skill_candidates: list[SkillCandidate] = Field(default_factory=list)

    # Meta
    uncertainties: list[Uncertainty] = Field(default_factory=list)
    review_priority: ReviewPriority = Field(default=ReviewPriority.medium, description="How important this video is for review")
    review_notes: Optional[str] = Field(default=None, description="Additional notes for the reviewer")


# --- Manifest / Index models ---

class ManifestEntry(BaseModel):
    """Entry in the run manifest."""
    video_id: str
    title: Optional[str] = None
    url: str
    status: VideoStatus = VideoStatus.pending
    output_folder: Optional[str] = None
    model: Optional[str] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None


class RunManifest(BaseModel):
    """Manifest for a processing run."""
    run_name: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    model: str
    playlist_url: Optional[str] = None
    playlist_name: Optional[str] = None
    videos: list[ManifestEntry] = Field(default_factory=list)


class ProcessedEntry(BaseModel):
    """Entry in the global processed index."""
    video_id: str
    last_processed: str
    model: str
    output_folder: str
    schema_version: str


class ProcessedIndex(BaseModel):
    """Global index of successfully processed videos."""
    entries: dict[str, ProcessedEntry] = Field(default_factory=dict, description="Keyed by video_id")


class ErrorRecord(BaseModel):
    """Record of a processing error."""
    video_url: str
    video_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    error_type: str
    error_message: str
    retryable: bool = False
