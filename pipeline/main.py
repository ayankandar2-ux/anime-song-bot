import os
import shutil
from datetime import datetime

from config import (
    PIPELINE_BOT_TOKEN, STORAGE_CHAT_ID, PUBLIC_CHANNEL_ID, DELIVERY_BOT_USERNAME,
    MAX_UPLOAD_AGE_HOURS,
)
from fetch import search_candidates, get_full_info, download_video, extract_audio, download_thumbnail
from dedupe import load_posted, save_posted
from supabase_store import put_song_record
from telegram_api import send_video, send_audio, send_photo_with_buttons

MAX_NEW_POSTS_PER_RUN = 3  # keep each run light and predictable


def translate_to_english(text):
    """Best-effort translation; falls back to the original text if translation fails."""
    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source="auto", target="en").translate(text)
        return translated or text
    except Exception as e:
        print(f"[translate] failed, using original title: {e}")
        return text


BLOCKED_TITLE_KEYWORDS = [
    "reaction", "reacts", "react to", "reacting",
    "review", "analysis", "explained", "breakdown",
    "cover by", "amv", "tier list", "ranking",
    "top 10", "top 20", "top 30", "top 50", "countdown", "best of",
]


def process_one(video_id, posted):
    info = get_full_info(video_id)
    title = info.get("title", "Unknown Title")
    artist = info.get("uploader", "Unknown Artist")
    thumbnail_url = info.get("thumbnail")

    title_lower = title.lower()
    if any(bad in title_lower for bad in BLOCKED_TITLE_KEYWORDS):
        print(f"[skip] {video_id} title looks like reaction/review content: {title}")
        posted[video_id] = {"skipped": "reaction_or_review"}
        return False

    upload_date = info.get("upload_date")  # format: YYYYMMDD
    if upload_date:
        uploaded_at = datetime.strptime(upload_date, "%Y%m%d")
        age_hours = (datetime.utcnow() - uploaded_at).total_seconds() / 3600
        if age_hours > MAX_UPLOAD_AGE_HOURS:
            print(f"[skip] {video_id} is {int(age_hours)}h old, over the {MAX_UPLOAD_AGE_HOURS}h limit")
            posted[video_id] = {"skipped": "too_old"}  # don't keep re-checking this one every run
            return False

    video_path = download_video(video_id)
    audio_path = extract_audio(video_path)
    thumb_path = download_thumbnail(thumbnail_url, video_id) if thumbnail_url else None

    # Upload originals to the private storage chat; capture message_id (works cross-bot via copyMessage)
    mp4_file_id, mp4_message_id = send_video(PIPELINE_BOT_TOKEN, STORAGE_CHAT_ID, video_path, caption=title)
    mp3_file_id, mp3_message_id = send_audio(
        PIPELINE_BOT_TOKEN, STORAGE_CHAT_ID, audio_path,
        caption=title, title=title, performer=artist,
    )

    # Store in Supabase so the delivery bot can find them later
    put_song_record(video_id, {
        "mp3_file_id": mp3_file_id,
        "mp4_file_id": mp4_file_id,
        "mp3_message_id": mp3_message_id,
        "mp4_message_id": mp4_message_id,
        "title": title,
        "artist": artist,
    })

    # Post the public preview with download buttons that deep-link to the delivery bot
    import html
    english_title = translate_to_english(title)
    safe_title_en = html.escape(english_title)
    safe_title_orig = html.escape(title)
    safe_artist = html.escape(artist)

    like_count = info.get("like_count")
    rating_line = f"👍 {like_count:,} likes" if like_count else "👍 rating unavailable"

    caption = (
        f"<b>{safe_title_en}</b>\n"
        f"<i>{safe_title_orig}</i>\n"
        f"{rating_line}\n"
        f"🎤 {safe_artist}"
    )
    buttons = [
        {"text": "⬇️ Download MP3", "url": f"https://t.me/{DELIVERY_BOT_USERNAME}?start={video_id}_mp3"},
        {"text": "⬇️ Download MP4", "url": f"https://t.me/{DELIVERY_BOT_USERNAME}?start={video_id}_mp4"},
    ]
    if thumb_path:
        send_photo_with_buttons(PIPELINE_BOT_TOKEN, PUBLIC_CHANNEL_ID, thumb_path, caption, buttons)

    posted[video_id] = {"title": title, "artist": artist}

    # Cleanup local files
    for p in (video_path, audio_path, thumb_path):
        if p and os.path.exists(p):
            os.remove(p)

    return True


def main():
    posted = load_posted()
    candidates = search_candidates()

    new_count = 0
    for c in candidates:
        if new_count >= MAX_NEW_POSTS_PER_RUN:
            break
        vid = c["id"]
        if not vid or vid in posted:
            continue
        try:
            was_posted = process_one(vid, posted)
            if was_posted:
                new_count += 1
        except Exception as e:
            print(f"Skipping {vid} due to error: {e}")

    save_posted(posted)
    print(f"Done. Posted {new_count} new song(s).")


if __name__ == "__main__":
    main()
