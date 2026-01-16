import json
import os
import re
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


def safe_read_existing() -> dict:
    if OUTFILE.exists():
        try:
            return json.loads(OUTFILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def write_json(payload: dict) -> None:
    OUTFILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("Wrote followers.json:", payload)


# -------------------------
# YouTube
# -------------------------
def fetch_youtube_subs(api_key: str, channel_id: str) -> int:
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


# -------------------------
# Instagram (scrape, no login)
# We parse og:description (most stable without tokens)
# Example content: "43 Followers, 1 Following, 0 Posts - See Instagram photos..."
# -------------------------
def parse_human_count(s: str) -> int:
    """
    Accepts: "1", "43", "1,234", "1.234", "12K", "12.3K", "1.2M"
    Returns integer count.
    """
    s = s.strip()

    # 12.3K / 1.2M etc
    m = re.match(r"^([0-9]+(?:[.,][0-9]+)?)\s*([KMB])$", s, re.IGNORECASE)
    if m:
        num = float(m.group(1).replace(",", "."))
        suf = m.group(2).upper()
        mult = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[suf]
        return int(num * mult)

    # remove thousand separators
    # if it contains both . and , we keep digits only
    digits = re.sub(r"[^\d]", "", s)
    return int(digits) if digits else 0


def fetch_instagram_followers(username: str) -> int:
    url = f"https://www.instagram.com/{username}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    r = requests.get(url, headers=headers, timeout=25)
    r.raise_for_status()
    html = r.text

    # Find og:description
    # <meta property="og:description" content="43 Followers, 1 Following, 0 Posts - See Instagram photos and videos from ...">
    m = re.search(
        r'<meta\s+property="og:description"\s+content="([^"]+)"',
        html,
        re.IGNORECASE,
    )
    if not m:
        raise RuntimeError("Could not find og:description (profile may be private, blocked, or HTML changed)")

    desc = m.group(1)
    # take first token up to space (usually the follower count)
    # sometimes it can be like "43 Followers, ..." so first token is "43"
    first = desc.split(" ", 1)[0]
    return parse_human_count(first)


def main() -> None:
    existing = safe_read_existing()

    yt_api_key = get_env("YT_API_KEY")
    yt_channel_id = get_env("YT_CHANNEL_ID")
    ig_username = get_env("IG_USERNAME")

    # YouTube
    yt = fetch_youtube_subs(yt_api_key, yt_channel_id)

    # Instagram (scrape). If it fails, keep previous value to avoid writing nonsense.
    try:
        ig = fetch_instagram_followers(ig_username)
    except Exception as e:
        print("Instagram fetch failed:", repr(e))
        ig = int(existing.get("instagram", 0) or 0)

    payload = {"youtube": int(yt), "instagram": int(ig)}
    write_json(payload)


if __name__ == "__main__":
    main()

