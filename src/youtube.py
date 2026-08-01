"""YouTube video and playlist metadata extraction using yt-dlp."""
import json
import subprocess
import logging
from dataclasses import dataclass

from .utils import extract_video_id, is_playlist_url

logger = logging.getLogger(__name__)


@dataclass
class VideoInfo:
    """Basic video metadata from YouTube."""
    video_id: str
    url: str
    title: str | None = None
    channel: str | None = None
    duration_seconds: int | None = None
    playlist_index: int | None = None
    playlist_name: str | None = None
    playlist_url: str | None = None


def parse_video_urls(text: str) -> list[str]:
    """Parse one or more YouTube URLs from text (one per line)."""
    urls = []
    for line in text.strip().splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            urls.append(line)
    return urls


def get_video_info(url: str) -> VideoInfo:
    """Get basic video metadata for a single URL using yt-dlp.
    
    Uses flat extraction (no download) to get title, channel, duration.
    """
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"Could not extract video ID from URL: {url}")
    
    canonical_url = f"https://www.youtube.com/watch?v={video_id}"
    
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--dump-json",
                "--no-download",
                "--no-playlist",
                "--no-warnings",
                canonical_url,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode != 0:
            logger.warning(f"yt-dlp failed for {url}: {result.stderr}")
            # Return basic info even if yt-dlp fails
            return VideoInfo(video_id=video_id, url=canonical_url)
        
        data = json.loads(result.stdout)
        return VideoInfo(
            video_id=video_id,
            url=canonical_url,
            title=data.get("title"),
            channel=data.get("uploader") or data.get("channel"),
            duration_seconds=data.get("duration"),
        )
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        logger.warning(f"Could not get metadata for {url}: {e}")
        return VideoInfo(video_id=video_id, url=canonical_url)


def extract_playlist(playlist_url: str) -> list[VideoInfo]:
    """Extract video entries from a YouTube playlist using yt-dlp flat extraction.
    
    Does NOT download any video content. Only extracts metadata.
    """
    if not is_playlist_url(playlist_url):
        raise ValueError(f"Not a valid playlist URL: {playlist_url}")
    
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--flat-playlist",
                "--dump-json",
                "--no-download",
                "--no-warnings",
                playlist_url,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp playlist extraction failed: {result.stderr}")
        
        videos = []
        # Get playlist title from first entry if available
        playlist_name = None
        
        for idx, line in enumerate(result.stdout.strip().splitlines(), 1):
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            video_id = data.get("id")
            if not video_id:
                continue
            
            if playlist_name is None:
                playlist_name = data.get("playlist_title") or data.get("playlist")
            
            videos.append(VideoInfo(
                video_id=video_id,
                url=f"https://www.youtube.com/watch?v={video_id}",
                title=data.get("title"),
                channel=data.get("uploader") or data.get("channel"),
                duration_seconds=data.get("duration"),
                playlist_index=idx,
                playlist_name=playlist_name,
                playlist_url=playlist_url,
            ))
        
        return videos
    
    except subprocess.TimeoutExpired:
        raise RuntimeError("Playlist extraction timed out. The playlist may be very large.")
    except FileNotFoundError:
        raise RuntimeError(
            "yt-dlp is not installed. Install it with: pip install yt-dlp"
        )


def resolve_input(text: str, mode: str) -> list[VideoInfo]:
    """Resolve input text into a list of VideoInfo based on mode.
    
    Args:
        text: The input text (URL or URLs)
        mode: 'single', 'multiple', or 'playlist'
    
    Returns:
        List of VideoInfo objects
    """
    if mode == "playlist":
        return extract_playlist(text.strip())
    
    urls = parse_video_urls(text) if mode == "multiple" else [text.strip()]
    
    videos = []
    for url in urls:
        video_id = extract_video_id(url)
        if video_id:
            try:
                info = get_video_info(url)
                videos.append(info)
            except Exception as e:
                logger.warning(f"Failed to get info for {url}: {e}")
                videos.append(VideoInfo(
                    video_id=video_id,
                    url=f"https://www.youtube.com/watch?v={video_id}",
                ))
    
    return videos
