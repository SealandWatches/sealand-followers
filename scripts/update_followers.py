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

# ---------- YouTube ----------
def fetch_youtube_subs(api_key: str, channel_id: str) -> int:
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {"part": "statistics", "id": channel_id, "key": api_key}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return int(r.json()["items"][0]["statistics"]["subscriberCount"])

# ---------- Instagram (scrape, no token) ----------
def parse_human_count(s: str) -> int:
    s = s.strip()
    m = re.match(r"^([0-9]+(?:[.,][0-9]+)?)\s*([KMB])$", s, re.IGNORECASE)
    if m:
        num = float(m.group(1).replace(",", "."))
        mult = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[m.group(2).upper()]
        return int(num * mult)
    digits = re.sub(r
