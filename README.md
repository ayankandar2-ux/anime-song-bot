# Anime Song Bot

Two-part system:
1. **Pipeline** (GitHub Actions, runs every 30 min) — finds new anime OP/ED songs,
   downloads them, converts to MP3+MP4, posts a preview (thumbnail + title + artist +
   download buttons) to your public Telegram channel.
2. **Delivery bot** (Cloudflare Worker) — when someone taps a download button, checks
   they've joined the channel, then sends the actual file.

## Setup order

### 1. Create a private "storage" chat
Make a private Telegram group or channel, add your **pipeline bot** as admin.
This is only used to store files and get reusable `file_id`s — nothing is posted here
publicly. Get its chat ID (forward a message from it to `@userinfobot`, or use
`getUpdates`).

### 2. Get your public channel's numeric ID and invite link
Add both bots as admins of your public channel (pipeline bot needs post permission,
delivery bot needs read permission to check membership).

### 3. Create a Cloudflare KV namespace
```
wrangler kv:namespace create SONGS_KV
```
Copy the namespace ID into `worker/wrangler.toml`.

### 4. Deploy the delivery bot
```
cd worker
wrangler secret put DELIVERY_BOT_TOKEN
wrangler secret put PUBLIC_CHANNEL_ID          # e.g. @myanimesongs or -100xxxxxxxxxx
wrangler secret put PUBLIC_CHANNEL_INVITE_LINK # e.g. https://t.me/myanimesongs
wrangler deploy
```
Then set the webhook so Telegram sends updates to your Worker:
```
curl "https://api.telegram.org/bot<DELIVERY_BOT_TOKEN>/setWebhook?url=<YOUR_WORKER_URL>"
```

### 5. Set GitHub repo secrets
Repo → Settings → Secrets and variables → Actions:
- `PIPELINE_BOT_TOKEN`
- `STORAGE_CHAT_ID`
- `PUBLIC_CHANNEL_ID`
- `DELIVERY_BOT_USERNAME` (no `@`)
- `CF_ACCOUNT_ID`
- `CF_KV_NAMESPACE_ID`
- `CF_API_TOKEN` (needs "Workers KV Storage: Edit" permission)

### 6. Push and test
Push this repo to GitHub, then trigger the workflow manually once from the
**Actions** tab ("Run workflow") to confirm everything works before letting the
cron schedule take over.

## Notes
- Repo should be **public** so GitHub Actions minutes are unlimited.
- Bot API file uploads are capped at 50MB — the download step already filters for this.
- `posted.json` is the dedupe log; it's committed back to the repo after every run.
