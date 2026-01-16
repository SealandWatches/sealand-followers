import json
import os
import sys
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
OUTFILE = ROOT / "followers.json"


def get_env(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        print(f"Missing env var: {name}", file=sys.stderr)
        sys.exit(1)
    return v


def fetch_youtube_subs(api_key: str, channel_id: str) -> int:
    # YouTube Data API: channels.list (part=statistics&id=...)
    # statistics.subscriberCount bestaat, maar YouTube kan counts afronden/aanpassen. :contentReference[oaicite:1]{index=1}
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {"part": "statistics", "id": channel_id, "key": api_key}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    items = data.get("items", [])
    if not items:
        raise RuntimeError(f"No channel found for id={channel_id}")
    stats = items[0].get("statistics", {})
    return int(stats.get("subscriberCount", 0))


def fetch_instagram_followers(access_token: str, ig_user_id: str) -> int:
    # Instagram Graph API IG User: fields=followers_count :contentReference[oaicite:2]{index=2}
    url = f"https://graph.facebook.com/v20.0/{ig_user_id}"
    params = {"fields": "followers_count", "access_token": access_token}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    return int(data.get("followers_count", 0))


def main() -> None:
    yt_api_key = get_env("YT_API_KEY")
    yt_channel_id = get_env("YT_CHANNEL_ID")
    ig_access_token = get_env("IG_ACCESS_TOKEN")
    ig_user_id = get_env("IG_USER_ID")

    yt = fetch_youtube_subs(yt_api_key, yt_channel_id)
    ig = fetch_instagram_followers(ig_access_token, ig_user_id)

    payload = {"youtube": yt, "instagram": ig}

    OUTFILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("Wrote followers.json:", payload)


if __name__ == "__main__":
    main()
