"""
Core Downloader Engine for StreamFlow
Handles:
- Universal multi-media (Videos, Music/Audio, Photos/Images, Carousels/Playlists)
- Resilient 500MB+ transfers with zero fragment loss
- 3-attempt automated retry for batch links
- 10+ concurrent items processing and ZIP packaging
- Automatic folder organization: moves big files into dedicated folders
"""

import os
import time
import zipfile
from typing import Dict, List, Optional, Callable
import requests
import yt_dlp

from core.security import verify_url_security
from core.utils import (
    sanitize_title_15,
    format_bytes,
    get_ffmpeg_path,
    organize_downloaded_file
)


def inspect_media_url(url: str) -> Dict:
    """Universal media inspector."""
    url = url.strip()

    is_safe, sec_msg, sec_report = verify_url_security(url)
    if not is_safe:
        return {
            "success": False,
            "security_passed": False,
            "error": sec_msg,
            "url": url
        }

    ffmpeg_exe = get_ffmpeg_path()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    # 1. Direct photo check
    image_exts = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp")
    url_lower = url.split("?")[0].lower()
    if any(url_lower.endswith(ext) for ext in image_exts):
        try:
            head = requests.head(url, headers=headers, allow_redirects=True, timeout=8)
            cl = int(head.headers.get("content-length", 0))
            raw_name = os.path.splitext(os.path.basename(url.split("?")[0]))[0] or "photo"
            ext = os.path.splitext(url.split("?")[0])[1].lstrip(".") or "jpg"
            return {
                "success": True,
                "media_type": "Photo",
                "media_icon": "🖼️",
                "url": url,
                "title": raw_name,
                "safe_name_15": sanitize_title_15(raw_name, ext),
                "thumbnail": url,
                "duration": "N/A (Image)",
                "resolution": "Original Image",
                "estimated_size": format_bytes(cl) if cl else "Full Resolution",
                "has_multiple_qualities": False,
                "direct_download": True,
                "qualities": [{
                    "label": f"Original Image ({format_bytes(cl)})",
                    "format_id": "direct_http",
                    "ext": ext,
                    "is_image": True
                }],
                "security_report": sec_report
            }
        except Exception:
            pass

    # 2. Extract using yt-dlp
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'skip_download': True,
        'ffmpeg_location': ffmpeg_exe,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'android_creator'],
                'player_skip': ['webpage', 'configs']
            }
        },
        'http_headers': headers
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        try:
            head = requests.head(url, headers=headers, allow_redirects=True, timeout=8)
            ct = head.headers.get("content-type", "")
            cl = int(head.headers.get("content-length", 0))
            if "video" in ct or "octet-stream" in ct or any(url_lower.endswith(ext) for ext in (".mp4", ".mkv", ".webm")):
                raw_name = os.path.splitext(os.path.basename(url.split("?")[0]))[0] or "video"
                return {
                    "success": True,
                    "media_type": "Video",
                    "media_icon": "📹",
                    "url": url,
                    "title": raw_name,
                    "safe_name_15": sanitize_title_15(raw_name, "mp4"),
                    "thumbnail": None,
                    "duration": "Direct Stream",
                    "resolution": "Native",
                    "estimated_size": format_bytes(cl) if cl else "Direct Stream",
                    "has_multiple_qualities": False,
                    "direct_download": True,
                    "qualities": [{
                        "label": f"Direct Stream ({format_bytes(cl)})",
                        "format_id": "direct_http",
                        "ext": "mp4"
                    }],
                    "security_report": sec_report
                }
        except Exception:
            pass

        return {
            "success": False,
            "security_passed": True,
            "error": f"Could not extract media info: {str(e)}",
            "url": url
        }

    # Check for playlists / carousels
    entries = info.get("entries")
    if entries:
        valid_entries = [e for e in entries if e]
        if len(valid_entries) > 1:
            return {
                "success": True,
                "media_type": "Multi-Item / Playlist",
                "media_icon": "📚",
                "is_multi_item": True,
                "item_count": len(valid_entries),
                "url": url,
                "title": info.get("title") or "Collection",
                "safe_name_15": sanitize_title_15(info.get("title") or "Collection", "zip"),
                "thumbnail": valid_entries[0].get("thumbnail") if valid_entries else None,
                "duration": f"{len(valid_entries)} items",
                "resolution": "Mixed",
                "estimated_size": f"{len(valid_entries)} media files",
                "has_multiple_qualities": False,
                "direct_download": True,
                "qualities": [{
                    "label": f"Download All {len(valid_entries)} Items (ZIP)",
                    "format_id": "best",
                    "ext": "zip"
                }],
                "security_report": sec_report,
                "entries": valid_entries
            }
        elif len(valid_entries) == 1:
            info = valid_entries[0]

    title = info.get("title") or "media"
    thumbnail = info.get("thumbnail")
    duration_secs = info.get("duration")
    duration_str = time.strftime('%M:%S', time.gmtime(duration_secs)) if duration_secs else "N/A"
    is_pure_audio = info.get("vcodec") == "none" or "music" in (info.get("extractor") or "").lower()

    raw_formats = info.get("formats", [])
    height_map = {}
    best_audio = None
    max_height = 0
    total_est_size = 0

    for f in raw_formats:
        vc = f.get("vcodec", "none")
        ac = f.get("acodec", "none")
        h = f.get("height")
        fs = f.get("filesize") or f.get("filesize_approx")

        if vc != "none" and h:
            max_height = max(max_height, h)
            if h not in height_map or (fs and not height_map[h].get("filesize")):
                height_map[h] = {"height": h, "filesize": fs, "ext": f.get("ext", "mp4")}
        if vc == "none" and ac != "none":
            if not best_audio or (fs and not best_audio.get("filesize")):
                best_audio = {"filesize": fs, "ext": "mp3"}

    sorted_heights = sorted(height_map.keys(), reverse=True)
    qualities = []

    if len(sorted_heights) > 1:
        top_h = sorted_heights[0]
        top_size = height_map[top_h].get("filesize")
        total_est_size = top_size or 0

        qualities.append({
            "label": f"🌟 Best Available ({top_h}p - {format_bytes(top_size)})",
            "format_id": "bestvideo+bestaudio/best",
            "height": 9999,
            "ext": "mp4",
            "size_str": format_bytes(top_size)
        })

        for h in sorted_heights:
            size_val = height_map[h].get("filesize")
            size_str = format_bytes(size_val) if size_val else "Available"
            if h >= 2160:
                name = f"2160p (4K UHD) - {size_str}"
            elif h >= 1440:
                name = f"1440p (2K QHD) - {size_str}"
            elif h >= 1080:
                name = f"1080p (Full HD) - {size_str}"
            elif h >= 720:
                name = f"720p (HD) - {size_str}"
            elif h >= 480:
                name = f"480p (SD) - {size_str}"
            else:
                name = f"{h}p - {size_str}"

            qualities.append({
                "label": f"✓ {name}",
                "format_id": f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/best",
                "height": h,
                "ext": "mp4",
                "size_str": size_str
            })

        audio_size = format_bytes(best_audio["filesize"]) if best_audio and best_audio.get("filesize") else "High Quality"
        qualities.append({
            "label": f"✓ Audio Only (MP3 320k) - {audio_size}",
            "format_id": "bestaudio/best",
            "height": 0,
            "ext": "mp3",
            "is_audio": True,
            "size_str": audio_size
        })

        has_multiple_qualities = True
    else:
        has_multiple_qualities = False
        fs = info.get("filesize") or info.get("filesize_approx")
        total_est_size = fs or 0
        ext = info.get("ext", "mp3" if is_pure_audio else "mp4")
        qualities.append({
            "label": f"✓ Direct Media Stream ({format_bytes(fs)})",
            "format_id": "best",
            "height": sorted_heights[0] if sorted_heights else 0,
            "ext": ext,
            "is_audio": is_pure_audio,
            "size_str": format_bytes(fs)
        })

    primary_ext = "mp3" if is_pure_audio else "mp4"
    safe_name = sanitize_title_15(title, primary_ext)
    resolution_str = f"{max_height}p" if max_height else ("Audio" if is_pure_audio else "Native")

    return {
        "success": True,
        "media_type": "Audio" if is_pure_audio else "Video",
        "media_icon": "🎵" if is_pure_audio else "📹",
        "url": url,
        "title": title,
        "safe_name_15": safe_name,
        "thumbnail": thumbnail,
        "duration": duration_str,
        "resolution": resolution_str,
        "estimated_size": format_bytes(total_est_size),
        "has_multiple_qualities": has_multiple_qualities,
        "direct_download": not has_multiple_qualities,
        "qualities": qualities,
        "security_report": sec_report
    }


def download_media_file(
    url: str,
    format_id: str,
    output_dir: str,
    is_audio: bool = False,
    is_image: bool = False,
    progress_callback: Optional[Callable[[Dict], None]] = None
) -> Dict:
    """Downloads and organizes media with big file folder relocation."""
    os.makedirs(output_dir, exist_ok=True)
    ffmpeg_exe = get_ffmpeg_path()

    if format_id == "direct_http" or is_image:
        return download_direct_http(url, output_dir, progress_callback)

    def ydl_hook(d):
        if not progress_callback:
            return
        status = d.get('status')
        if status == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed') or 0
            eta = d.get('eta') or 0
            pct = (downloaded / total * 100) if total else 0
            progress_callback({
                'status': 'downloading',
                'percent': pct,
                'downloaded': downloaded,
                'total': total,
                'speed': speed,
                'eta': eta,
                'downloaded_str': format_bytes(downloaded),
                'total_str': format_bytes(total),
                'speed_str': f"{speed / (1024 * 1024):.2f} MB/s" if speed else "Calculating...",
                'eta_str': f"{eta}s" if eta else "Calculating..."
            })
        elif status == 'finished':
            progress_callback({
                'status': 'merging',
                'percent': 99.0,
                'message': 'Merging high quality streams via FFmpeg...'
            })

    token = f"{int(time.time() * 1000)}_{os.getpid()}"
    temp_tmpl = os.path.join(output_dir, f"tmp_{token}.%(ext)s")

    ydl_opts = {
        'format': format_id,
        'outtmpl': temp_tmpl,
        'progress_hooks': [ydl_hook],
        'ffmpeg_location': ffmpeg_exe,
        'nocheckcertificate': True,
        'retries': 20,
        'fragment_retries': 20,
        'skip_unavailable_fragments': False,
        'buffersize': 4 * 1024 * 1024,
        'http_chunk_size': 10485760,
        'continuedl': True,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'android_creator'],
                'player_skip': ['webpage', 'configs']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }

    if is_audio and ffmpeg_exe:
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            extract_data = ydl.extract_info(url, download=True)
            raw_title = extract_data.get('title', 'media')

        generated_files = [
            f for f in os.listdir(output_dir)
            if f.startswith(f"tmp_{token}") and not f.endswith(".part") and not f.endswith(".ytdl")
        ]

        if not generated_files:
            return {"success": False, "error": "Media downloaded but output file not found on disk."}

        temp_filename = generated_files[0]
        temp_filepath = os.path.join(output_dir, temp_filename)
        _, ext = os.path.splitext(temp_filename)
        ext = ext.lstrip(".")

        safe_filename = sanitize_title_15(raw_title, ext)
        intermediate_filepath = os.path.join(output_dir, safe_filename)

        os.rename(temp_filepath, intermediate_filepath)

        # Integrity check
        file_size = os.path.getsize(intermediate_filepath)
        if file_size == 0:
            os.remove(intermediate_filepath)
            return {"success": False, "error": "Downloaded file size was 0 bytes (integrity check failed)."}

        # Automatic Folder Movement: Move big files to dedicated folder
        m_type = "Audio" if is_audio else ("Photo" if ext in ("jpg", "png", "webp", "jpeg") else "Video")
        final_filepath, subfolder, final_filename = organize_downloaded_file(
            intermediate_filepath, output_dir, media_type=m_type
        )

        return {
            "success": True,
            "file_path": final_filepath,
            "filename": final_filename,
            "subfolder": subfolder,
            "original_title": raw_title,
            "file_size": file_size,
            "file_size_str": format_bytes(file_size),
            "mime_type": "audio/mpeg" if ext == "mp3" else ("image/jpeg" if ext in ("jpg", "jpeg") else "video/mp4")
        }

    except Exception as e:
        for f in os.listdir(output_dir):
            if f.startswith(f"tmp_{token}"):
                try:
                    os.remove(os.path.join(output_dir, f))
                except Exception:
                    pass
        return {"success": False, "error": f"Download failed: {str(e)}"}


def download_direct_http(url: str, output_dir: str, progress_callback: Optional[Callable[[Dict], None]] = None) -> Dict:
    """Direct chunked HTTP downloader with folder relocation."""
    try:
        basename = os.path.basename(url.split("?")[0]) or "media.mp4"
        raw_name, ext = os.path.splitext(basename)
        safe_filename = sanitize_title_15(raw_name, ext or "mp4")
        temp_path = os.path.join(output_dir, safe_filename)

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, stream=True, timeout=30, headers=headers)
        resp.raise_for_status()

        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        chunk_size = 1024 * 1024
        start_time = time.time()

        with open(temp_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total > 0:
                        elapsed = max(time.time() - start_time, 0.1)
                        speed = downloaded / elapsed
                        pct = (downloaded / total) * 100
                        progress_callback({
                            'status': 'downloading',
                            'percent': pct,
                            'downloaded': downloaded,
                            'total': total,
                            'speed_str': f"{speed / (1024*1024):.2f} MB/s",
                            'downloaded_str': format_bytes(downloaded),
                            'total_str': format_bytes(total)
                        })

        final_size = os.path.getsize(temp_path)
        ext_clean = ext.lstrip(".").lower()
        is_photo = ext_clean in ("jpg", "jpeg", "png", "webp", "gif")
        m_type = "Photo" if is_photo else "Video"
        
        final_filepath, subfolder, final_filename = organize_downloaded_file(
            temp_path, output_dir, media_type=m_type
        )

        mime = "image/png" if ext_clean == "png" else ("image/jpeg" if ext_clean in ("jpg", "jpeg") else "video/mp4")
        return {
            "success": True,
            "file_path": final_filepath,
            "filename": final_filename,
            "subfolder": subfolder,
            "original_title": raw_name,
            "file_size": final_size,
            "file_size_str": format_bytes(final_size),
            "mime_type": mime
        }
    except Exception as e:
        return {"success": False, "error": f"Direct download failed: {str(e)}"}


def download_with_retry(
    url: str,
    format_id: str,
    output_dir: str,
    is_audio: bool = False,
    is_image: bool = False,
    max_retries: int = 3
) -> Dict:
    """Executes download with up to max_retries attempts."""
    last_error = ""
    for attempt in range(1, max_retries + 1):
        res = download_media_file(
            url=url,
            format_id=format_id,
            output_dir=output_dir,
            is_audio=is_audio,
            is_image=is_image,
            progress_callback=None
        )
        if res.get("success"):
            res["attempts"] = attempt
            return res
        last_error = res.get("error", "Unknown error")
        time.sleep(1.0 * attempt)

    return {
        "success": False,
        "error": f"Failed after {max_retries} attempts. Reason: {last_error}",
        "url": url,
        "attempts": max_retries
    }


def create_zip_archive(file_paths: List[str], zip_output_path: str) -> bool:
    """Creates a zip archive and moves to batch/ subfolder."""
    try:
        with zipfile.ZipFile(zip_output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for fp in file_paths:
                if os.path.exists(fp):
                    zipf.write(fp, arcname=os.path.basename(fp))
        return True
    except Exception:
        return False


def cleanup_old_files(directory: str, max_age_hours: int = 2):
    """Recursively purges server-side temporary downloads older than max_age_hours."""
    if not os.path.exists(directory):
        return
    now = time.time()
    cutoff = now - (max_age_hours * 3600)
    for root, _, files in os.walk(directory):
        for f in files:
            fpath = os.path.join(root, f)
            try:
                if os.path.getmtime(fpath) < cutoff:
                    os.remove(fpath)
            except Exception:
                pass
