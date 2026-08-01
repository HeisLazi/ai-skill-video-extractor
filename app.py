"""AI Skill Video Extractor - Streamlit Application."""
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

from src.config import (
    get_api_key, get_model, mask_api_key,
    SCHEMA_VERSION, DEFAULT_MODEL, DEFAULT_OUTPUT_DIR,
)
from src.schemas import (
    VideoSource, ManifestEntry, RunManifest, ErrorRecord, VideoStatus,
)
from src.youtube import VideoInfo, resolve_input
from src.gemini_client import analyze_video, APIStats
from src.exporter import (
    create_run_directory, save_source_json, save_analysis_json,
    save_manifest, append_error, create_video_directory, save_readme,
)
from src.renderer import render_review_md, render_run_summary
from src.index import (
    load_index, save_index, is_already_processed, mark_processed,
)
from src.utils import format_duration


# --- Page config ---
st.set_page_config(
    page_title="AI Skill Video Extractor",
    page_icon="🎬",
    layout="wide",
)


# --- Session state initialization ---
def init_session_state():
    defaults = {
        "session_api_key": "",
        "discovered_videos": [],
        "selected_indices": [],
        "processing": False,
        "run_results": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session_state()


# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Settings")

    # API Key
    st.subheader("API Key")
    env_key = get_api_key()
    if env_key:
        st.success(f"🔑 Environment key: {mask_api_key(env_key)}")
    else:
        st.warning("No GEMINI_API_KEY in .env")

    session_key_input = st.text_input(
        "Session API Key (overrides .env)",
        type="password",
        value=st.session_state.session_api_key,
        key="api_key_input",
    )
    if session_key_input != st.session_state.session_api_key:
        st.session_state.session_api_key = session_key_input

    active_key = get_api_key(st.session_state.session_api_key)
    if active_key:
        st.info(f"Active key: {mask_api_key(active_key)}")
    else:
        st.error("❌ No API key configured")

    st.divider()

    # Model
    st.subheader("Model")
    model = st.text_input("Gemini Model", value=get_model(), key="model_input")

    st.divider()

    # Output
    st.subheader("Output")
    output_dir = st.text_input("Output Directory", value=DEFAULT_OUTPUT_DIR, key="output_dir")
    run_name = st.text_input("Run Name (optional)", value="", key="run_name")

    st.divider()

    # Processing options
    st.subheader("Processing Options")
    skip_processed = st.checkbox("Skip already processed videos", value=True, key="skip_processed")
    retry_failed = st.checkbox("Retry previously failed videos", value=False, key="retry_failed")
    max_videos = st.number_input("Max videos this run", min_value=1, max_value=500, value=50, key="max_videos")


# --- Main UI ---
st.title("🎬 AI Skill Video Extractor")
st.caption("Turn useful YouTube videos into structured evidence for later Agent Skill review.")

st.divider()

# Input mode selection
mode = st.radio(
    "Input Mode",
    ["Single Video", "Multiple Videos", "Playlist"],
    horizontal=True,
    key="input_mode",
)

# Input area
if mode == "Single Video":
    url_input = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
        key="single_url",
    )
elif mode == "Multiple Videos":
    url_input = st.text_area(
        "YouTube URLs (one per line)",
        placeholder="https://www.youtube.com/watch?v=abc123\nhttps://www.youtube.com/watch?v=def456",
        height=150,
        key="multi_urls",
    )
else:  # Playlist
    url_input = st.text_input(
        "Playlist URL",
        placeholder="https://www.youtube.com/playlist?list=...",
        key="playlist_url",
    )

# Discover videos button
if st.button("🔍 Discover Videos", type="secondary", disabled=not url_input):
    if not url_input or not url_input.strip():
        st.error("Please enter a URL.")
    else:
        mode_map = {
            "Single Video": "single",
            "Multiple Videos": "multiple",
            "Playlist": "playlist",
        }
        with st.spinner("Discovering videos..."):
            try:
                videos = resolve_input(url_input, mode_map[mode])
                if not videos:
                    st.error("No valid videos found. Check your URL(s).")
                else:
                    st.session_state.discovered_videos = videos
                    st.session_state.selected_indices = list(range(len(videos)))
                    st.success(f"Found {len(videos)} video(s)")
            except Exception as e:
                st.error(f"Error discovering videos: {e}")
                st.session_state.discovered_videos = []

# Display discovered videos
videos = st.session_state.discovered_videos
if videos:
    st.divider()
    st.subheader(f"📋 Discovered Videos ({len(videos)})")

    # Select all / deselect all
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Select All"):
            st.session_state.selected_indices = list(range(len(videos)))
            st.rerun()
    with col2:
        if st.button("Deselect All"):
            st.session_state.selected_indices = []
            st.rerun()

    # Load index for skip-processed checking
    processed_index = load_index(st.session_state.get("output_dir", DEFAULT_OUTPUT_DIR))

    # Video list with checkboxes
    selected = []
    for i, video in enumerate(videos):
        already_done = is_already_processed(processed_index, video.video_id)
        status_badge = " ✅ (already processed)" if already_done and skip_processed else ""

        label = f"**{video.title or video.video_id}**"
        if video.channel:
            label += f" — {video.channel}"
        if video.duration_seconds:
            label += f" ({format_duration(video.duration_seconds)})"
        label += status_badge

        checked = st.checkbox(
            label,
            value=(i in st.session_state.selected_indices),
            key=f"video_select_{i}",
        )
        if checked:
            selected.append(i)

    st.session_state.selected_indices = selected

    selected_count = len(selected)
    effective_count = min(selected_count, st.session_state.get("max_videos", 50))

    st.info(f"Selected: {selected_count} | Will process: {effective_count} (max: {st.session_state.get('max_videos', 50)})")

    # --- Start Analysis ---
    st.divider()

    can_start = (
        active_key
        and selected_count > 0
        and not st.session_state.processing
    )

    if st.button("🚀 Start Analysis", type="primary", disabled=not can_start):
        st.session_state.processing = True

        # Determine videos to process
        selected_videos = [videos[i] for i in selected[:effective_count]]

        # Check skip-processed
        if skip_processed:
            filtered = []
            skipped_ids = []
            for v in selected_videos:
                if is_already_processed(processed_index, v.video_id):
                    skipped_ids.append(v.video_id)
                else:
                    filtered.append(v)
            if skipped_ids:
                st.info(f"Skipping {len(skipped_ids)} already-processed video(s)")
        else:
            filtered = selected_videos
            skipped_ids = []

        # Create run directory
        rn = run_name if run_name else None
        run_dir = create_run_directory(output_dir, rn)
        actual_run_name = run_dir.name

        # Initialize manifest
        playlist_url_val = url_input.strip() if mode == "Playlist" else None
        playlist_name_val = videos[0].playlist_name if videos and videos[0].playlist_name else None

        manifest = RunManifest(
            run_name=actual_run_name,
            model=model,
            playlist_url=playlist_url_val,
            playlist_name=playlist_name_val,
        )

        # Add all selected videos to manifest
        for v in selected_videos:
            status = VideoStatus.skipped if v.video_id in skipped_ids else VideoStatus.pending
            manifest.videos.append(ManifestEntry(
                video_id=v.video_id,
                title=v.title,
                url=v.url,
                status=status,
                model=model,
            ))

        # Save initial manifest
        save_manifest(run_dir, manifest)
        save_readme(run_dir, actual_run_name, model, playlist_url_val)

        # Progress tracking
        stats = APIStats()
        analyses = {}  # video_id -> (source, analysis)
        total_to_process = len(filtered)
        success_count = 0
        fail_count = 0

        # Progress UI
        st.subheader("📊 Processing")
        progress_bar = st.progress(0)
        status_text = st.empty()
        detail_container = st.container()

        for idx, video in enumerate(filtered):
            video_num = idx + 1
            progress = video_num / total_to_process if total_to_process > 0 else 1.0
            progress_bar.progress(progress)

            status_text.markdown(
                f"**Processing {video_num}/{total_to_process}:** "
                f"{video.title or video.video_id} "
                f"([link]({video.url}))"
            )

            # Find manifest entry
            manifest_entry = None
            for me in manifest.videos:
                if me.video_id == video.video_id:
                    manifest_entry = me
                    break

            if manifest_entry:
                manifest_entry.status = VideoStatus.processing

            start_time = time.time()

            # Create video directory
            video_dir = create_video_directory(
                run_dir, video_num, video.title, video.video_id
            )

            # Build source metadata
            source = VideoSource(
                video_id=video.video_id,
                url=video.url,
                title=video.title,
                channel=video.channel,
                playlist_name=video.playlist_name,
                playlist_url=video.playlist_url,
                playlist_index=video.playlist_index,
                duration_seconds=video.duration_seconds,
                analysis_model=model,
            )
            save_source_json(video_dir, source)

            # Run Gemini analysis
            result = analyze_video(
                api_key=active_key,
                video_url=video.url,
                model=model,
                stats=stats,
            )

            elapsed = time.time() - start_time

            if result.success and result.analysis:
                # Save analysis
                save_analysis_json(video_dir, result.analysis)

                # Render REVIEW.md
                review_md = render_review_md(source, result.analysis)
                (video_dir / "REVIEW.md").write_text(review_md, encoding="utf-8")

                # Update manifest
                if manifest_entry:
                    manifest_entry.status = VideoStatus.success
                    manifest_entry.output_folder = video_dir.name
                    manifest_entry.timestamp = datetime.utcnow().isoformat()

                # Update index
                mark_processed(
                    processed_index, video.video_id, model,
                    str(video_dir), SCHEMA_VERSION,
                )
                save_index(output_dir, processed_index)

                # Track for summary
                analyses[video.video_id] = (source, result.analysis)
                success_count += 1

                with detail_container:
                    st.success(
                        f"✅ {video.title or video.video_id} — "
                        f"{elapsed:.1f}s, priority: {result.analysis.review_priority.value}"
                    )
            else:
                # Record failure
                error_msg = result.error or "Unknown error"
                if manifest_entry:
                    manifest_entry.status = VideoStatus.failed
                    manifest_entry.error = error_msg
                    manifest_entry.timestamp = datetime.utcnow().isoformat()

                append_error(run_dir, ErrorRecord(
                    video_url=video.url,
                    video_id=video.video_id,
                    error_type=result.error_type or "Unknown",
                    error_message=error_msg,
                    retryable=result.retryable,
                ))

                fail_count += 1

                with detail_container:
                    st.error(
                        f"❌ {video.title or video.video_id} — "
                        f"{error_msg[:100]}"
                    )

            # Save manifest after each video
            save_manifest(run_dir, manifest)

        # Generate run summary
        summary_md = render_run_summary(manifest, analyses)
        (run_dir / "run-summary.md").write_text(summary_md, encoding="utf-8")

        # Final manifest save
        save_manifest(run_dir, manifest)

        # Results
        progress_bar.progress(1.0)
        status_text.empty()

        st.divider()
        st.subheader("🏁 Run Complete")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("✅ Successful", success_count)
        col2.metric("❌ Failed", fail_count)
        col3.metric("⏭️ Skipped", len(skipped_ids))
        col4.metric("📊 Total", success_count + fail_count + len(skipped_ids))

        st.info(f"📂 Results saved to: `{run_dir}`")

        if stats.total_input_tokens > 0 or stats.total_output_tokens > 0:
            st.caption(
                f"API Stats — Requests: {stats.requests_attempted} attempted, "
                f"{stats.requests_successful} successful, {stats.requests_failed} failed | "
                f"Tokens: {stats.total_input_tokens:,} in, {stats.total_output_tokens:,} out"
            )
        else:
            st.caption(
                f"API Stats — Requests: {stats.requests_attempted} attempted, "
                f"{stats.requests_successful} successful, {stats.requests_failed} failed"
            )

        st.session_state.processing = False
        st.session_state.run_results = {
            "run_dir": str(run_dir),
            "success": success_count,
            "failed": fail_count,
            "skipped": len(skipped_ids),
        }

# Footer
st.divider()
st.caption(
    "v0.1 · Gemini analysis is candidate knowledge — "
    "GPT/human review required before adoption into skill library."
)
