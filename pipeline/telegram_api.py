import requests

API_BASE = "https://api.telegram.org/bot{token}/{method}"


def _call(token, method, data=None, files=None):
    url = API_BASE.format(token=token, method=method)
    resp = requests.post(url, data=data, files=files, timeout=120)
    resp.raise_for_status()
    result = resp.json()
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error on {method}: {result}")
    return result["result"]


def send_video(token, chat_id, file_path, caption=None):
    with open(file_path, "rb") as f:
        result = _call(
            token, "sendVideo",
            data={"chat_id": chat_id, "caption": caption or ""},
            files={"video": f},
        )
    return result["video"]["file_id"]


def send_audio(token, chat_id, file_path, caption=None, title=None, performer=None):
    with open(file_path, "rb") as f:
        data = {"chat_id": chat_id, "caption": caption or ""}
        if title:
            data["title"] = title
        if performer:
            data["performer"] = performer
        result = _call(token, "sendAudio", data=data, files={"audio": f})
    return result["audio"]["file_id"]


def send_photo_with_buttons(token, chat_id, photo_path, caption, buttons):
    """
    buttons: list of {"text": ..., "url": ...} dicts, one row each
    """
    import json
    keyboard = {"inline_keyboard": [[b] for b in buttons]}
    with open(photo_path, "rb") as f:
        result = _call(
            token, "sendPhoto",
            data={
                "chat_id": chat_id,
                "caption": caption,
                "reply_markup": json.dumps(keyboard),
                "parse_mode": "HTML",
            },
            files={"photo": f},
        )
    return result
