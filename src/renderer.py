"""Local rendering of Markdown review files from analysis JSON.

No Gemini API calls. All rendering is done locally from structured data.
"""
from collections import Counter
from pathlib import Path

from .schemas import (
    VideoAnalysis, VideoSource, ManifestEntry, RunManifest, VideoStatus,
)


def render_review_md(source: VideoSource, analysis: VideoAnalysis) -> str:
    """Render REVIEW.md from source and analysis data."""
    lines = []
    
    lines.append("# Video Review")
    lines.append("")
    
    # Source section
    lines.append("## Source")
    lines.append("")
    lines.append(f"- **Title:** {analysis.title}")
    if source.channel:
        lines.append(f"- **Creator:** {source.channel}")
    lines.append(f"- **URL:** {source.url}")
    lines.append(f"- **Model:** {source.analysis_model or 'unknown'}")
    lines.append(f"- **Schema Version:** {analysis.schema_version}")
    lines.append(f"- **Prompt Version:** {analysis.prompt_version}")
    if source.duration_seconds:
        mins = source.duration_seconds // 60
        secs = source.duration_seconds % 60
        lines.append(f"- **Duration:** {mins}:{secs:02d}")
    if source.playlist_name:
        lines.append(f"- **Playlist:** {source.playlist_name}")
    lines.append("")
    
    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(analysis.summary)
    lines.append("")
    if analysis.thesis:
        lines.append(f"**Thesis:** {analysis.thesis}")
        lines.append("")
    if analysis.audience:
        lines.append(f"**Audience:** {analysis.audience}")
        lines.append("")
    if analysis.topics:
        lines.append(f"**Topics:** {', '.join(analysis.topics)}")
        lines.append("")
    if analysis.tools_shown:
        lines.append(f"**Tools Shown:** {', '.join(analysis.tools_shown)}")
        lines.append("")
    
    # Review Priority
    lines.append(f"**Review Priority:** {analysis.review_priority.value.upper()}")
    if analysis.review_notes:
        lines.append(f"\n> {analysis.review_notes}")
    lines.append("")
    
    # Candidate Principles
    if analysis.candidate_principles:
        lines.append("## Candidate Principles")
        lines.append("")
        for i, p in enumerate(analysis.candidate_principles, 1):
            lines.append(f"### {i}. {p.name}")
            lines.append("")
            lines.append(f"**Explanation:** {p.explanation}")
            lines.append("")
            lines.append(f"**Why It Matters:** {p.why_it_matters}")
            lines.append("")
            lines.append(f"**Context:** {p.context}")
            lines.append("")
            if p.does_not_apply_when:
                lines.append(f"**Do Not Use When:** {p.does_not_apply_when}")
                lines.append("")
            lines.append(f"**Evidence:** {p.evidence_type.value} | **Confidence:** {p.confidence.value}")
            if p.timestamp:
                lines.append(f"**Timestamp:** {p.timestamp}")
            lines.append("")
    
    # Techniques
    if analysis.techniques:
        lines.append("## Techniques")
        lines.append("")
        for i, t in enumerate(analysis.techniques, 1):
            lines.append(f"### {i}. {t.name}")
            lines.append("")
            lines.append(f"{t.description}")
            lines.append("")
            if t.steps:
                lines.append("**Steps:**")
                for j, step in enumerate(t.steps, 1):
                    lines.append(f"{j}. {step}")
                lines.append("")
            if t.intended_result:
                lines.append(f"**Intended Result:** {t.intended_result}")
                lines.append("")
            if t.prerequisites:
                lines.append(f"**Prerequisites:** {', '.join(t.prerequisites)}")
                lines.append("")
            if t.tools_involved:
                lines.append(f"**Tools:** {', '.join(t.tools_involved)}")
                lines.append("")
            lines.append(f"**AI Agent Reusable:** {'Yes' if t.reusable_by_ai_agent else 'No'} | **Confidence:** {t.confidence.value}")
            if t.timestamp:
                lines.append(f"**Timestamp:** {t.timestamp}")
            lines.append("")
    
    # Visual Observations
    if analysis.visual_observations:
        lines.append("## Visual Observations")
        lines.append("")
        for i, v in enumerate(analysis.visual_observations, 1):
            lines.append(f"### {i}. {v.what_changed}")
            lines.append("")
            if v.before:
                lines.append(f"**Before:** {v.before}")
            if v.after:
                lines.append(f"**After:** {v.after}")
            if v.likely_reason:
                lines.append(f"**Likely Reason:** {v.likely_reason}")
            if v.observed_effect:
                lines.append(f"**Observed Effect:** {v.observed_effect}")
            lines.append(f"**Confidence:** {v.confidence.value}")
            if v.timestamp:
                lines.append(f"**Timestamp:** {v.timestamp}")
            lines.append("")
    
    # Coding Observations
    if analysis.coding_observations:
        lines.append("## Coding Observations")
        lines.append("")
        for i, c in enumerate(analysis.coding_observations, 1):
            lines.append(f"### {i}. [{c.category}] {c.observation}")
            lines.append("")
            if c.details:
                lines.append(f"{c.details}")
                lines.append("")
            rec_str = "Explicitly recommended" if c.explicitly_recommended else "Inferred from implementation"
            lines.append(f"**Source:** {rec_str} | **Confidence:** {c.confidence.value}")
            if c.timestamp:
                lines.append(f"**Timestamp:** {c.timestamp}")
            lines.append("")
    
    # Workflows
    if analysis.workflows:
        lines.append("## Workflows")
        lines.append("")
        for i, w in enumerate(analysis.workflows, 1):
            lines.append(f"### {i}. {w.name}")
            lines.append("")
            lines.append(f"**Purpose:** {w.purpose}")
            lines.append("")
            if w.trigger:
                lines.append(f"**When to Use:** {w.trigger}")
                lines.append("")
            if w.steps:
                lines.append("**Steps:**")
                for step in w.steps:
                    lines.append(f"{step.step_number}. {step.action}")
                    if step.details:
                        lines.append(f"   _{step.details}_")
                lines.append("")
            if w.exit_condition:
                lines.append(f"**Exit Condition:** {w.exit_condition}")
                lines.append("")
            if w.mistakes_to_avoid:
                lines.append("**Mistakes to Avoid:**")
                for m in w.mistakes_to_avoid:
                    lines.append(f"- {m}")
                lines.append("")
            lines.append(f"**Confidence:** {w.confidence.value}")
            if w.timestamp:
                lines.append(f"**Timestamp:** {w.timestamp}")
            lines.append("")
    
    # Before/After Examples
    if analysis.before_after_examples:
        lines.append("## Before / After Examples")
        lines.append("")
        for i, ba in enumerate(analysis.before_after_examples, 1):
            lines.append(f"### Example {i}")
            lines.append("")
            lines.append(f"**Original State:** {ba.original_state}")
            lines.append("")
            lines.append(f"**Problem Identified:** {ba.identified_problem}")
            lines.append("")
            lines.append(f"**Modification:** {ba.modification}")
            lines.append("")
            lines.append(f"**Result:** {ba.result}")
            lines.append("")
            if ba.principle_demonstrated:
                lines.append(f"**Principle Demonstrated:** {ba.principle_demonstrated}")
            if ba.timestamp:
                lines.append(f"**Timestamp:** {ba.timestamp}")
            lines.append("")
    
    # Anti-patterns
    if analysis.anti_patterns:
        lines.append("## Anti-patterns")
        lines.append("")
        for i, ap in enumerate(analysis.anti_patterns, 1):
            lines.append(f"### {i}. {ap.name}")
            lines.append("")
            lines.append(f"**Why Problematic:** {ap.why_problematic}")
            lines.append("")
            if ap.better_alternative:
                lines.append(f"**Better Alternative:** {ap.better_alternative}")
                lines.append("")
            if ap.context:
                lines.append(f"**Context:** {ap.context}")
            lines.append(f"**Confidence:** {ap.confidence.value}")
            if ap.timestamp:
                lines.append(f"**Timestamp:** {ap.timestamp}")
            lines.append("")
    
    # Candidate Agent Behaviors
    if analysis.candidate_agent_behaviors:
        lines.append("## Candidate Agent Behaviors")
        lines.append("")
        for i, b in enumerate(analysis.candidate_agent_behaviors, 1):
            lines.append(f"### {i}. {b.behavior}")
            lines.append("")
            lines.append(f"**Trigger:** {b.trigger}")
            lines.append("")
            lines.append(f"**Action:** {b.action}")
            lines.append("")
            lines.append(f"**Expected Outcome:** {b.expected_outcome}")
            lines.append("")
            if b.supporting_evidence:
                lines.append(f"**Evidence:** {b.supporting_evidence}")
            lines.append(f"**Confidence:** {b.confidence.value}")
            lines.append("")
    
    # Candidate Skill Categories
    if analysis.candidate_skill_categories:
        lines.append("## Candidate Skill Categories")
        lines.append("")
        for cat in analysis.candidate_skill_categories:
            lines.append(f"- `{cat}`")
        lines.append("")
    
    # Skill Candidates
    if analysis.skill_candidates:
        lines.append("## Potential Skills")
        lines.append("")
        for i, sc in enumerate(analysis.skill_candidates, 1):
            lines.append(f"### {i}. {sc.skill_name}")
            lines.append("")
            lines.append(f"**Description:** {sc.description}")
            lines.append("")
            lines.append(f"**Evidence:** {sc.evidence_from_video}")
            lines.append("")
            if sc.possible_triggers:
                lines.append(f"**Triggers:** {', '.join(sc.possible_triggers)}")
                lines.append("")
            lines.append(f"**Would Teach:** {sc.what_skill_would_teach}")
            lines.append("")
            lines.append(f"**Disposition:** {sc.disposition.value}")
            lines.append("")
    
    # Uncertainties
    if analysis.uncertainties:
        lines.append("## Uncertainties / Needs Review")
        lines.append("")
        for i, u in enumerate(analysis.uncertainties, 1):
            lines.append(f"### {i}. {u.topic}")
            lines.append("")
            lines.append(f"{u.details}")
            lines.append("")
            lines.append(f"**Category:** {u.category}")
            lines.append("")
    
    # GPT Review Status
    lines.append("## GPT Review Status")
    lines.append("")
    lines.append("- [ ] Reviewed by GPT")
    lines.append("- [ ] Accepted into knowledge library")
    lines.append("- [ ] Rejected")
    lines.append("- [ ] Needs more sources")
    lines.append("- [ ] Candidate skill created")
    lines.append("")
    
    return "\n".join(lines)


def render_run_summary(
    manifest: RunManifest,
    analyses: dict[str, tuple[VideoSource, VideoAnalysis]],
) -> str:
    """Render run-summary.md from manifest and analysis data.
    
    Args:
        manifest: The run manifest
        analyses: Dict of video_id -> (source, analysis) for successful videos
    """
    lines = []
    
    # Header
    lines.append(f"# Run Summary: {manifest.run_name}")
    lines.append("")
    lines.append(f"**Date:** {manifest.created_at}")
    lines.append(f"**Model:** {manifest.model}")
    if manifest.playlist_url:
        lines.append(f"**Playlist:** {manifest.playlist_url}")
        if manifest.playlist_name:
            lines.append(f"**Playlist Name:** {manifest.playlist_name}")
    lines.append("")
    
    # Counts
    success_count = sum(1 for v in manifest.videos if v.status == VideoStatus.success)
    failed_count = sum(1 for v in manifest.videos if v.status == VideoStatus.failed)
    skipped_count = sum(1 for v in manifest.videos if v.status == VideoStatus.skipped)
    total = len(manifest.videos)
    
    lines.append("## Results")
    lines.append("")
    lines.append(f"| Metric | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| ✅ Successful | {success_count} |")
    lines.append(f"| ❌ Failed | {failed_count} |")
    lines.append(f"| ⏭️ Skipped | {skipped_count} |")
    lines.append(f"| **Total** | **{total}** |")
    lines.append("")
    
    # Video table
    lines.append("## Videos")
    lines.append("")
    lines.append("| # | Video | Creator | Status | Categories | Review Priority | Folder |")
    lines.append("|---|-------|---------|--------|------------|-----------------|--------|")
    
    for entry in manifest.videos:
        status_emoji = {
            VideoStatus.success: "✅",
            VideoStatus.failed: "❌",
            VideoStatus.skipped: "⏭️",
            VideoStatus.pending: "⏳",
            VideoStatus.processing: "🔄",
        }.get(entry.status, "❓")
        
        title = entry.title or entry.video_id
        if len(title) > 50:
            title = title[:47] + "..."
        
        categories = ""
        priority = ""
        
        if entry.video_id in analyses:
            _, analysis = analyses[entry.video_id]
            if analysis.candidate_skill_categories:
                cats = analysis.candidate_skill_categories[:3]
                categories = ", ".join(cats)
                if len(analysis.candidate_skill_categories) > 3:
                    categories += f" (+{len(analysis.candidate_skill_categories) - 3})"
            priority = analysis.review_priority.value
        
        folder = entry.output_folder or ""
        
        lines.append(
            f"| {manifest.videos.index(entry) + 1} | {title} | "
            f"{''} | {status_emoji} {entry.status.value} | "
            f"{categories} | {priority} | `{folder}` |"
        )
    lines.append("")
    
    # Cross-video themes (aggregated locally, no Gemini call)
    if analyses:
        lines.append("## Potential Cross-Video Themes")
        lines.append("")
        lines.append("_Aggregated from individual analyses. Deeper synthesis by GPT recommended._")
        lines.append("")
        
        # Category counts
        category_counter = Counter()
        skill_names = []
        for vid_id, (src, analysis) in analyses.items():
            for cat in analysis.candidate_skill_categories:
                category_counter[cat] += 1
            for sc in analysis.skill_candidates:
                skill_names.append(sc.skill_name)
        
        if category_counter:
            lines.append("### Category Frequency")
            lines.append("")
            for cat, count in category_counter.most_common():
                lines.append(f"- `{cat}` — {count} video{'s' if count > 1 else ''}")
            lines.append("")
        
        if skill_names:
            lines.append("### Skill Candidates Across Videos")
            lines.append("")
            for name in skill_names:
                lines.append(f"- {name}")
            lines.append("")
    
    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*This summary was generated locally from structured analysis data.*")
    lines.append("*Gemini's analysis is candidate knowledge — GPT/human review is required before adoption.*")
    lines.append("")
    
    return "\n".join(lines)
