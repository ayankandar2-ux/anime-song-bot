import requests

from config import SUPABASE_URL, SUPABASE_KEY


def put_song_record(song_id, record):
    """record: dict like {"mp3_file_id": ..., "mp4_file_id": ..., "title": ..., "artist": ...}"""
    url = f"{SUPABASE_URL}/rest/v1/anime_song_files"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates",
    }
    payload = {"song_id": song_id, **record}
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp
