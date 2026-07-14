import subprocess
import json
import os

from config import SEARCH_KEYWORDS, RESULTS_PER_KEYWORD

COOKIES_PATH = "cookies.txt"
_cookie_args = ["--cookies", COOKIES_PATH] if os.path.exists(COOKIES_PATH) else []


PLAYER_CLIENTS_TO_TRY = ["ios", "android", "web_safari", "mweb"]


def _run_with_client_fallback(base_cmd, url, timeout):
    """Try yt-dlp with several player clients until one works."""
    last_error = None
    for client in PLAYER_CLIENTS_TO_TRY:
        cmd = base_cmd + _cookie_args + [
            "--remote-components", "ejs:github",
            "--extractor-args", f"youtube:player_client={client}",
            url,
        ]
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=True)
        except subprocess.CalledProcessError as e:
            last_error = e
            print(f"[client fallback] '{client}' failed, trying next client: {(e.stderr or '')[:200]}")
            continue
    raise last_error


def search_candidates():
    """Search YouTube for anime song videos, return list of dicts (deduped)."""
    candidates = []

    for keyword in SEARCH_KEYWORDS:
        query = f"ytsearch{RESULTS_PER_KEYWORD}:{keyword}"
        base_cmd = ["yt-dlp", "-j", "--flat-playlist"]
        try:
            out = _run_with_client_fallback(base_cmd, query, timeout=60)
        except subprocess.CalledProcessError as e:
            print(f"[search] '{keyword}' failed: {(e.stderr or '')[:500]}")
            continue

        print(f"[search] '{keyword}' returned {len(out.stdout.strip().splitlines())} raw lines")

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

    seen = set()
    unique_candidates = []
    for c in candidates:
        if c["id"] and c["id"] not in seen:
            seen.add(c["id"])
            unique_candidates.append(c)
    return unique_candidates


def get_full_info(video_id):
    """Fetch full metadata (upload date, thumbnail, uploader) for a specific video."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    base_cmd = ["yt-dlp", "-j"]
    try:
        out = _run_with_client_fallback(base_cmd, url, timeout=60)
    except subprocess.CalledProcessError as e:
        print(f"[info] {video_id} failed: {(e.stderr or '')[:500]}")
        raise
    return json.loads(out.stdout)


def download_video(video_id, out_dir="downloads"):
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{video_id}.mp4")
    url = f"https://www.youtube.com/watch?v={video_id}"
    base_cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", out_path,
    ]
    _run_with_client_fallback(base_cmd, url, timeout=300)

    if os.path.exists(out_path) and os.path.getsize(out_path) > 49 * 1024 * 1024:
        raise RuntimeError(f"Downloaded file for {video_id} exceeds Telegram's 50MB bot upload limit")

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
