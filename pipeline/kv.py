import requests

from config import CF_ACCOUNT_ID, CF_KV_NAMESPACE_ID, CF_API_TOKEN

KV_URL = (
    "https://api.cloudflare.com/client/v4/accounts/{account_id}/storage/kv/namespaces/"
    "{namespace_id}/values/{key}"
)


def put_song_record(song_id, record):
    """record: dict like {"mp3_file_id": ..., "mp4_file_id": ..., "title": ..., "artist": ...}"""
    import json
    url = KV_URL.format(
        account_id=CF_ACCOUNT_ID,
        namespace_id=CF_KV_NAMESPACE_ID,
        key=f"song:{song_id}",
    )
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}"}
    resp = requests.put(url, headers=headers, data=json.dumps(record), timeout=30)
    resp.raise_for_status()
    return resp.json()
