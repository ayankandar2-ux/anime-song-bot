import os

# --- Telegram ---
PIPELINE_BOT_TOKEN = os.environ["PIPELINE_BOT_TOKEN"]       # bot that posts to the public channel
STORAGE_CHAT_ID = os.environ["STORAGE_CHAT_ID"]             # private chat/channel used only to get file_ids
PUBLIC_CHANNEL_ID = os.environ["PUBLIC_CHANNEL_ID"]         # your public channel, e.g. @myanimesongs
DELIVERY_BOT_USERNAME = os.environ["DELIVERY_BOT_USERNAME"] # e.g. AnimeSongDeliveryBot (no @)

# --- Cloudflare KV (so the delivery bot can look up file_ids) ---
CF_ACCOUNT_ID = os.environ["CF_ACCOUNT_ID"]
CF_KV_NAMESPACE_ID = os.environ["CF_KV_NAMESPACE_ID"]
CF_API_TOKEN = os.environ["CF_API_TOKEN"]

# --- Search behavior ---
SEARCH_KEYWORDS = [
    "anime opening 2026",
    "anime ending 2026",
    "anime OP full",
    "anime ED full",
]
RESULTS_PER_KEYWORD = 5
MAX_UPLOAD_AGE_HOURS = 48  # only consider videos uploaded within this window

POSTED_LOG = "posted.json"
