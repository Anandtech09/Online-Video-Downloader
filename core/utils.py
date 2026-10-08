"""
Utility Functions for StreamFlow
Handles title sanitation, byte formatting, FFmpeg detection, and automatic folder organization for big files.
"""

import os
import re
import shutil
from typing import Optional, Tuple

try:
    import imageio_ffmpeg
    BUNDLED_FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    BUNDLED_FFMPEG = None


def get_ffmpeg_path() -> Optional[str]:
    """Locate FFmpeg executable."""
    if BUNDLED_FFMPEG and os.path.exists(BUNDLED_FFMPEG):
        return BUNDLED_FFMPEG
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg
    return None


def sanitize_title_15(title: str, ext: str = "mp4") -> str:
    """
    Enforces title truncation policy:
    If title exceeds 15 characters, splice the base name to max 15 characters,
    preserving the clean file extension.
    """
    if not title:
        title = "media"

    clean = re.sub(r'[\\/*?:"<>|\n\r\t]', "", title)
    clean = re.sub(r'\s+', " ", clean).strip()
    if not clean:
        clean = "media"

    if len(clean) > 15:
        clean = clean[:15].strip()

    clean = clean.rstrip(". ")
    ext = ext.lstrip(".")
    if not ext:
        ext = "mp4"
    return f"{clean}.{ext}"


def format_bytes(num_bytes: Optional[int]) -> str:
    """Format bytes into readable size."""
    if num_bytes is None:
        return "Unknown size"
    if num_bytes <= 0:
        return "0 MB"
    mb = num_bytes / (1024 * 1024)
    if mb >= 1024:
        return f"{mb / 1024:.2f} GB"
    return f"{mb:.1f} MB"


def organize_downloaded_file(
    file_path: str,
    base_downloads_dir: str,
    media_type: str = "Video"
) -> Tuple[str, str, str]:
    """
    Folder organization system:
    When files are downloaded, creates dedicated category folders and moves them:
    - Big files (>= 100MB or 500MB): moved to 'large_files/'
    - ZIP / Multi-file archives: moved to 'batch/'
    - Audio / Music: moved to 'audio/'
    - Photos: moved to 'photos/'
    - Standard videos: moved to 'videos/'

    Returns (new_absolute_path, subfolder_name, filename).
    """
    if not os.path.exists(file_path):
        return file_path, "", os.path.basename(file_path)

    filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    # 100 MB threshold (100 * 1024 * 1024 bytes)
    is_big_file = file_size >= (100 * 1024 * 1024)

    if is_big_file:
        subfolder = "large_files"
    elif filename.endswith(".zip") or media_type.lower() == "batch":
        subfolder = "batch"
    elif media_type.lower() == "audio" or filename.endswith(".mp3") or filename.endswith(".m4a"):
        subfolder = "audio"
    elif media_type.lower() == "photo" or filename.lower().endswith((".jpg", ".png", ".webp", ".jpeg")):
        subfolder = "photos"
    else:
        subfolder = "videos"

    target_dir = os.path.join(base_downloads_dir, subfolder)
    os.makedirs(target_dir, exist_ok=True)

    target_path = os.path.join(target_dir, filename)

    # If file is not already in the target subfolder, move it
    if os.path.abspath(file_path) != os.path.abspath(target_path):
        if os.path.exists(target_path):
            base, ext = os.path.splitext(filename)
            target_path = os.path.join(target_dir, f"{base}_{int(os.path.getmtime(file_path)) % 1000}{ext}")
            filename = os.path.basename(target_path)
        shutil.move(file_path, target_path)

    return target_path, subfolder, filename
