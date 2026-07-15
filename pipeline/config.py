import os

# --- Telegram ---
PIPELINE_BOT_TOKEN = os.environ["PIPELINE_BOT_TOKEN"]       # bot that posts to the public channel
STORAGE_CHAT_ID = os.environ["STORAGE_CHAT_ID"]             # private chat/channel used only to get file_ids
PUBLIC_CHANNEL_ID = os.environ["PUBLIC_CHANNEL_ID"]         # your public channel, e.g. @myanimesongs
DELIVERY_BOT_USERNAME = os.environ["DELIVERY_BOT_USERNAME"] # e.g. AnimeSongDeliveryBot (no @)

# --- Supabase (so the delivery bot can look up file_ids) ---
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

# --- Search behavior ---
OFFICIAL_CHANNELS = [
    "https://www.youtube.com/@aniplex/videos",
    "https://www.youtube.com/@PONYCANYON_anime/videos",
    "https://www.youtube.com/c/LantisGlobalChannel/videos",
]
RESULTS_PER_CHANNEL = 6

SEARCH_KEYWORDS = [
    "anime opening 2026",
    "anime ending 2026",
    "anime OP full",
    "anime ED full",
    "anime opening 2025",
    "anime ending 2025",
    "new anime opening song",
    "new anime ending song",
    "anime OP full lyrics",
    "anime ED full lyrics",
]
RESULTS_PER_KEYWORD = 8
MAX_UPLOAD_AGE_HOURS = 720  # 30 days - regular search returns relevance-ranked results, not strictly newest

POSTED_LOG = "posted.json"
