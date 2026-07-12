import subprocess
import json
import time
import os

from config import SEARCH_KEYWORDS, RESULTS_PER_KEYWORD, MAX_UPLOAD_AGE_HOURS


def search_candidates():
    """Search YouTube for recent anime song videos, return list of dicts."""
    candidates = []
    cutoff = time.time() - MAX_UPLOAD_AGE_HOURS * 3600

    for keyword in SEARCH_KEYWORDS:
        query = f"ytsearchdate{RESULTS_PER_KEYWORD}:{keyword}"
        cmd = ["yt-dlp", "-j", "--flat-playlist", query]
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=True)
        except subprocess.CalledProcessError:
            continue

        for line in out.stdout.strip().splitlines():
            try:
                info = json.loads(line)
            except json.JSONDecodeError:
                continue
            candidates.append({
                "id": info.get("id"),
                "title": info.get("title"),
                "url": f"https://www.youtube.com/watch?v={info.get('id')}",
            })

    return candidates


def get_full_info(video_id):
    """Fetch full metadata (upload date, thumbnail, uploader) for a specific video."""
    cmd = ["yt-dlp", "-j", f"https://www.youtube.com/watch?v={video_id}"]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=True)
    return json.loads(out.stdout)


def download_video(video_id, out_dir="downloads"):
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{video_id}.mp4")
    cmd = [
        "yt-dlp",
        "-f", "best[ext=mp4][filesize<48M]/best[ext=mp4]",
        "-o", out_path,
        f"https://www.youtube.com/watch?v={video_id}",
    ]
    subprocess.run(cmd, check=True, timeout=300)
    return out_path


def extract_audio(video_path, out_dir="downloads"):
    audio_path = video_path.replace(".mp4", ".mp3")
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "libmp3lame", "-q:a", "2",
        audio_path,
    ]
    subprocess.run(cmd, check=True, timeout=120)
    return audio_path


def download_thumbnail(thumbnail_url, video_id, out_dir="downloads"):
    import requests
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{video_id}_thumb.jpg")
    r = requests.get(thumbnail_url, timeout=30)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)
    return path
