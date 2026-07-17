import os
import html

from config import (
    PIPELINE_BOT_TOKEN, STORAGE_CHAT_ID, PUBLIC_CHANNEL_ID, DELIVERY_BOT_USERNAME,
)
from animethemes_source import search_candidates, download_theme_video, extract_audio, extract_thumbnail
from thumbnail_overlay import make_banner_thumbnail
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


def process_one(candidate, posted):
    song_id = candidate["id"]
    title = candidate["title"]
    artist = candidate["artist"]
    anime_name = candidate["anime_name"]
    theme_type = candidate.get("theme_type") or ""

    video_path = download_theme_video(candidate["video_link"], song_id)
    audio_path = extract_audio(video_path)
    thumb_path = extract_thumbnail(video_path, song_id)

    display_title = title if title and title != "Unknown Theme" else f"{anime_name} {theme_type}"

    # Upload originals to the private storage chat; capture message_id (works cross-bot via copyMessage)
    mp4_file_id, mp4_message_id = send_video(PIPELINE_BOT_TOKEN, STORAGE_CHAT_ID, video_path, caption=display_title)
    mp3_file_id, mp3_message_id = send_audio(
        PIPELINE_BOT_TOKEN, STORAGE_CHAT_ID, audio_path,
        caption=display_title, title=display_title, performer=artist,
    )

    # Store in Supabase so the delivery bot can find them later
    put_song_record(song_id, {
        "mp3_file_id": mp3_file_id,
        "mp4_file_id": mp4_file_id,
        "mp3_message_id": mp3_message_id,
        "mp4_message_id": mp4_message_id,
        "title": display_title,
        "artist": artist,
    })

    # Post the public preview with download buttons that deep-link to the delivery bot
    english_title = translate_to_english(display_title)
    safe_title_en = html.escape(english_title)
    safe_title_orig = html.escape(display_title)
    safe_artist = html.escape(artist)
    safe_anime = html.escape(anime_name)

    caption = (
        f"<b>{safe_title_en}</b>\n"
        f"<i>{safe_title_orig}</i>\n"
        f"━━━━━━━━━━━━\n"
        f"📺 {safe_anime} ({theme_type})\n"
        f"🎤 <b>{safe_artist}</b>"
    )
    buttons = [
        {"text": "• Download MP3 •", "url": f"https://t.me/{DELIVERY_BOT_USERNAME}?start={song_id}_mp3"},
        {"text": "• Download MP4 •", "url": f"https://t.me/{DELIVERY_BOT_USERNAME}?start={song_id}_mp4"},
    ]

    banner_path = None
    if thumb_path:
        try:
            banner_path = make_banner_thumbnail(thumb_path, english_title, artist)
            print(f"[banner] created successfully: {banner_path}")
        except Exception as e:
            print(f"[banner] failed, using plain thumbnail: {e}")
            banner_path = thumb_path

    if banner_path:
        send_photo_with_buttons(PIPELINE_BOT_TOKEN, PUBLIC_CHANNEL_ID, banner_path, caption, buttons)

    posted[song_id] = {"title": display_title, "artist": artist, "anime": anime_name}

    # Cleanup local files
    for p in (video_path, audio_path, thumb_path, banner_path if banner_path != thumb_path else None):
        if p and os.path.exists(p):
            os.remove(p)

    return True


def main():
    posted = load_posted()
    candidates = search_candidates()
    print(f"Found {len(candidates)} candidate(s) from AnimeThemes.moe")

    new_count = 0
    for c in candidates:
        if new_count >= MAX_NEW_POSTS_PER_RUN:
            break
        song_id = c["id"]
        if song_id in posted:
            continue
        try:
            was_posted = process_one(c, posted)
            if was_posted:
                new_count += 1
        except Exception as e:
            print(f"Skipping {song_id} due to error: {e}")

    save_posted(posted)
    print(f"Done. Posted {new_count} new song(s).")


if __name__ == "__main__":
    main()
