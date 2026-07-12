// Cloudflare Worker: Telegram delivery bot
// Env vars needed (set via `wrangler secret put` or dashboard):
//   DELIVERY_BOT_TOKEN, PUBLIC_CHANNEL_ID (e.g. @myanimesongs), PUBLIC_CHANNEL_INVITE_LINK
// KV binding needed (set in wrangler.toml): SONGS_KV

export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      return new Response("OK");
    }

    const update = await request.json();
    const api = (method, body) =>
      fetch(`https://api.telegram.org/bot${env.DELIVERY_BOT_TOKEN}/${method}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

    try {
      if (update.message && update.message.text && update.message.text.startsWith("/start")) {
        await handleStart(update.message, env, api);
      } else if (update.callback_query) {
        await handleCallback(update.callback_query, env, api);
      }
    } catch (err) {
      console.error(err);
    }

    return new Response("OK");
  },
};

async function handleStart(message, env, api) {
  const chatId = message.chat.id;
  const parts = message.text.split(" ");
  const payload = parts[1]; // "<song_id>_<mp3|mp4>"

  if (!payload) {
    await api("sendMessage", { chat_id: chatId, text: "Welcome! Use a download link from the channel to get started." });
    return;
  }

  const isMember = await checkMembership(chatId, env);
  if (!isMember) {
    await promptJoin(chatId, payload, env, api);
    return;
  }

  await deliverFile(chatId, payload, env, api);
}

async function handleCallback(cb, env, api) {
  const chatId = cb.message.chat.id;
  const data = cb.data; // "check_<payload>"
  const payload = data.replace("check_", "");

  const isMember = await checkMembership(chatId, env);
  if (!isMember) {
    await api("answerCallbackQuery", { callback_query_id: cb.id, text: "You haven't joined yet!", show_alert: true });
    return;
  }

  await api("answerCallbackQuery", { callback_query_id: cb.id, text: "Verified! Sending your file..." });
  await deliverFile(chatId, payload, env, api);
}

async function checkMembership(userId, env) {
  const resp = await fetch(
    `https://api.telegram.org/bot${env.DELIVERY_BOT_TOKEN}/getChatMember?chat_id=${encodeURIComponent(env.PUBLIC_CHANNEL_ID)}&user_id=${userId}`
  );
  const data = await resp.json();
  if (!data.ok) return false;
  const status = data.result.status;
  return ["member", "administrator", "creator"].includes(status);
}

async function promptJoin(chatId, payload, env, api) {
  await api("sendMessage", {
    chat_id: chatId,
    text: "Join our channel first to unlock your download:",
    reply_markup: {
      inline_keyboard: [
        [{ text: "📢 Join Channel", url: env.PUBLIC_CHANNEL_INVITE_LINK }],
        [{ text: "✅ I've Joined, Check Again", callback_data: `check_${payload}` }],
      ],
    },
  });
}

async function deliverFile(chatId, payload, env, api) {
  const [songId, format] = payload.split("_");
  const record = await env.SONGS_KV.get(`song:${songId}`, { type: "json" });

  if (!record) {
    await api("sendMessage", { chat_id: chatId, text: "Sorry, this file is no longer available." });
    return;
  }

  if (format === "mp3") {
    await api("sendAudio", {
      chat_id: chatId,
      audio: record.mp3_file_id,
      title: record.title,
      performer: record.artist,
    });
  } else {
    await api("sendVideo", { chat_id: chatId, video: record.mp4_file_id, caption: record.title });
  }
}
