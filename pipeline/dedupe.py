import json
import os

from config import POSTED_LOG


def load_posted():
    if not os.path.exists(POSTED_LOG):
        return {}
    with open(POSTED_LOG, "r") as f:
        return json.load(f)


def save_posted(posted):
    with open(POSTED_LOG, "w") as f:
        json.dump(posted, f, indent=2)
