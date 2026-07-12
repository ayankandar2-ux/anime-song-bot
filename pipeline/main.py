import os
import shutil

from config import (
    PIPELINE_BOT_TOKEN, STORAGE_CHAT_ID, PUBLIC_CHANNEL_ID, DELIVERY_BOT_USERNAME,
)
from fetch import search_candidates, get_full_info, download_video, extract_audio, download_thumbnail
from dedupe import load_posted, save_posted
from kv import put_song_record
from telegram_api import send_video, send_audio, send_photo_with_buttons

MAX_NEW_POSTS_PER_RUN = 3  # keep each run light and predictable


def process_one(video_id, posted):
    info = get_full_info(video_id)
    title = info.get("title", "Unknown Title")
    artist = info.get("uploader", "Unknown Artist")
    thumbnail_url = info.get("thumbnail")

    video_path = download_video(video_id)
    audio_path = extract_audio(video_path)
    thumb_path = download_thumbnail(thumbnail_url, video_id) if thumbnail_url else None

    # Upload originals to the private storage chat to obtain reusable file_ids
    mp4_file_id = send_video(PIPELINE_BOT_TOKEN, STORAGE_CHAT_ID, video_path, caption=title)
    mp3_file_id = send_audio(
        PIPELINE_BOT_TOKEN, STORAGE_CHAT_ID, audio_path,
        caption=title, title=title, performer=artist,
    )

    # Store the file_ids in Cloudflare KV so the delivery bot can find them later
    put_song_record(video_id, {
        "mp3_file_id": mp3_file_id,
        "mp4_file_id": mp4_file_id,
        "title": title,
        "artist": artist,
    })

    # Post the public preview with download buttons that deep-link to the delivery bot
    caption = f"<b>{title}</b>\n🎤 {artist}"
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
            process_one(vid, posted)
            new_count += 1
        except Exception as e:
            print(f"Skipping {vid} due to error: {e}")

    save_posted(posted)
    print(f"Done. Posted {new_count} new song(s).")


if __name__ == "__main__":
    main()
