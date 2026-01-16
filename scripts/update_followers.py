import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUTFILE = ROOT / "followers.json"


def get_env(name: str, required: bool = False) -> str:
    v = os.getenv(name, "").strip()
    if required and not v:
        print(f"Missing env var: {name}", file=sys.stderr)
        sys.exit(1)
    return v


def to_int(value: str, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except Exception:
        return default


def fetch_youtube_subscribers(api_key: str, channel_id: str) -> int:
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {"part": "statistics", "id": channel_id, "key": api_key}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    items = data.get("items", [])
    if not items:
        return 0

    stats = items[0].get("statistics", {})
    return to_int(stats.get("subscriberCount", 0), 0)


def main() -> None:
    yt_api_key = get_env("YT_API_KEY", required=True)
    yt_channel_id = get_env("YT_CHANNEL_ID", required=True)

    # Instagram: zonder API is dit vaak instabiel.
    # Daarom doen we dit als handmatig getal via secret IG_FOLLOWERS (kan ook leeg blijven).
    ig_followers = to_int(get_env("IG_FOLLOWERS", required=False) or "0")

    yt_subs = 0
    try:
        yt_subs = fetch_youtube_subscribers(yt_api_key, yt_channel_id)
    except Exception as e:
        print(f"YouTube fetch failed: {e}", file=sys.stderr)
        yt_subs = 0

    payload = {
        "youtube": yt_subs,
        "instagram": ig_followers,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": {
            "youtube": "YouTube Data API v3",
            "instagram": "manual (IG_FOLLOWERS secret)",
        },
    }

    OUTFILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("Wrote followers.json:", payload)


if __name__ == "__main__":
    main()
