import os
import subprocess
import requests

ANIMETHEMES_API_BASE = "https://api.animethemes.moe"
PAGE_SIZE = 20


def search_candidates():
    """
    Query AnimeThemes.moe for confirmed anime OP/ED themes with clean (creditless)
    video links. Every result here is a database-verified anime song - no guessing
    from video titles needed.
    """
    url = f"{ANIMETHEMES_API_BASE}/animetheme"
    params = {
        "include": "anime,song.artists,animethemeentries.videos",
        "sort": "-id",  # most recently added to the database first
        "page[size]": PAGE_SIZE,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    candidates = []
    for theme in data.get("animethemes", []):
        anime = theme.get("anime") or {}
        song = theme.get("song") or {}
        artists = song.get("artists") or []
        artist_name = artists[0]["name"] if artists else (anime.get("name", "Unknown Artist"))
        song_title = song.get("title") or f"{theme.get('type', '')}{theme.get('sequence') or ''}"

        # A theme can have many video variants (different quality/cuts) - take only the
        # first clean match so the same song doesn't get posted repeatedly under different IDs
        chosen_video = None
        for entry in (theme.get("animethemeentries") or []):
            for video in (entry.get("videos") or []):
                if not video.get("nc"):  # skip versions with credits overlay; prefer clean
                    continue
                if video.get("lyrics"):  # skip versions with lyrics burned into the video
                    continue
                chosen_video = video
                break
            if chosen_video:
                break

        if not chosen_video:
            continue

        candidates.append({
            "id": f"at{theme['id']}",  # keyed on the theme itself, not the video variant
            "video_link": chosen_video["link"],
            "anime_name": anime.get("name", "Unknown Anime"),
            "title": song_title,
            "artist": artist_name,
            "theme_type": theme.get("type"),  # "OP" or "ED"
        })
    return candidates


def download_theme_video(video_link, video_id, out_dir="downloads"):
    """Download the WebM directly from AnimeThemes' own servers - no scraping needed."""
    os.makedirs(out_dir, exist_ok=True)
    webm_path = os.path.join(out_dir, f"{video_id}.webm")
    resp = requests.get(video_link, timeout=120, stream=True)
    resp.raise_for_status()
    with open(webm_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)

    # Convert to mp4 (h264/aac) for Telegram/mobile compatibility
    mp4_path = os.path.join(out_dir, f"{video_id}.mp4")
    cmd = [
        "ffmpeg", "-y", "-i", webm_path,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        mp4_path,
    ]
    subprocess.run(cmd, check=True, timeout=300)
    os.remove(webm_path)
    return mp4_path


def extract_audio(video_path, out_dir="downloads"):
    audio_path = video_path.replace(".mp4", ".mp3")
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "libmp3lame", "-q:a", "2",
        audio_path,
    ]
    subprocess.run(cmd, check=True, timeout=120)
    return audio_path


def extract_thumbnail(video_path, video_id, out_dir="downloads"):
    """Grab a frame from partway into the video to use as the post thumbnail."""
    thumb_path = os.path.join(out_dir, f"{video_id}_thumb.jpg")
    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-ss", "00:00:05", "-vframes", "1",
        thumb_path,
    ]
    subprocess.run(cmd, check=True, timeout=60)
    return thumb_path
