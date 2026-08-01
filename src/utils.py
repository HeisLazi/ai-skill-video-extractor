"""Utility functions."""
import re
import unicodedata


def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats.
    
    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/v/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    - URLs with additional parameters
    """
    if not url:
        return None
    
    url = url.strip()
    
    patterns = [
        r'(?:youtube\.com/watch\?.*v=)([a-zA-Z0-9_-]{11})',
        r'(?:youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def make_slug(text: str, max_length: int = 50) -> str:
    """Create a filesystem-safe slug from text."""
    if not text:
        return "untitled"
    
    # Normalize unicode
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Lowercase and replace non-alphanumeric with hyphens
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = text.strip('-')
    
    # Truncate
    if len(text) > max_length:
        text = text[:max_length].rstrip('-')
    
    return text or "untitled"


def make_video_folder_name(index: int, title: str | None, video_id: str) -> str:
    """Create folder name like: 001_great-dashboard-design_dQw4w9WgXcQ"""
    slug = make_slug(title or "untitled")
    return f"{index:03d}_{slug}_{video_id}"


def is_valid_youtube_url(url: str) -> bool:
    """Check if a URL looks like a valid YouTube URL."""
    return extract_video_id(url) is not None


def is_playlist_url(url: str) -> bool:
    """Check if a URL is a YouTube playlist URL."""
    if not url:
        return False
    return 'list=' in url and 'youtube.com' in url


def format_duration(seconds: int | None) -> str:
    """Format duration in seconds to H:MM:SS or M:SS."""
    if seconds is None:
        return "unknown"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
