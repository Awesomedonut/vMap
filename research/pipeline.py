#!/usr/bin/env python3
"""vMap market-research pipeline — one CLI over all research data sources.

Sources: Google News RSS (free), Google Trends via pytrends (free, flaky),
X/Twitter v2 (PAID per post on archive), YouTube Data API (free quota),
Steam/SteamSpy (free), Hacker News Algolia (free).

Usage:
    python3 pipeline.py news "fantasy map generator"
    python3 pipeline.py trends "fantasy map generator,inkarnate,azgaar"
    python3 pipeline.py x "inkarnate (wish OR expensive)" --archive --max 100
    python3 pipeline.py yt-search "fantasy map maker"
    python3 pipeline.py yt-comments VIDEO_ID --max 200
    python3 pipeline.py steam "Dungeon Alchemist"
    python3 pipeline.py hn "interactive map"
    python3 pipeline.py all "fantasy maps"      # every free source at once

Keys: put X_BEARER_TOKEN / YOUTUBE_API_KEY in research/.env (gitignored).
Cost: X full-archive/recent search bills ~$0.005 per post returned — the CLI
prints the estimated cost and refuses --max > 500 without --yes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "out"
X_COST_PER_POST = 0.005

# ---------------------------------------------------------------- env / http

def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    for path in (HERE / ".env",):
        if path.exists():
            for line in path.read_text().splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, _, v = line.partition("=")
                    env[k.strip()] = v.strip()
    return env

ENV = load_env()

def http_json(url: str, headers: dict | None = None) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "vmap-research/0.2", **(headers or {})})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)

def save(name: str, data) -> Path:
    OUT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = OUT_DIR / f"{stamp}-{re.sub(r'[^a-z0-9]+', '-', name.lower())[:50]}.json"
    path.write_text(json.dumps(data, indent=1, default=str))
    return path

# ------------------------------------------------------------------- sources

def news(query: str, max_items: int = 12) -> list[dict]:
    """Google News hidden RSS — no key needed."""
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        root = ElementTree.parse(r).getroot()
    items = []
    for item in root.iter("item"):
        src = item.find("source")
        items.append({"date": (item.findtext("pubDate") or "")[:16],
                      "source": src.text if src is not None else "?",
                      "title": item.findtext("title") or "",
                      "link": item.findtext("link") or ""})
    return items[:max_items]


def trends(keywords: list[str], timeframe: str = "today 5-y") -> dict:
    """Google Trends via pytrends. Warms a browser cookie first (avoids 429s)."""
    try:
        import requests
        from pytrends.request import TrendReq
    except ImportError:
        sys.exit("pytrends missing: research/.venv/bin/pip install pytrends "
                 "(then run with research/.venv/bin/python)")
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"})
    s.get("https://trends.google.com/trends/", timeout=20)
    pt = TrendReq(hl="en-US", tz=0, requests_args={"headers": dict(s.headers)})
    pt.cookies = s.cookies.get_dict()
    last_err = None
    for attempt in range(3):
        try:
            pt.build_payload(keywords[:5], timeframe=timeframe)
            df = pt.interest_over_time()
            if df.empty:
                return {"error": "empty result"}
            yearly = df.resample("YS").mean().round(1).drop(columns=["isPartial"], errors="ignore")
            recent = df.tail(13).drop(columns=["isPartial"], errors="ignore").mean().round(1)
            return {"yearly_avg": {str(k)[:10]: v for k, v in yearly.to_dict("index").items()},
                    "last_13w_avg": recent.to_dict()}
        except Exception as e:  # Google 429s freely; retry with backoff
            last_err = e
            time.sleep(20 * (attempt + 1))
    return {"error": f"trends failed after retries: {str(last_err)[:200]}"}


def x_search(query: str, archive: bool, max_results: int, start: str = "2015-01-01") -> list[dict]:
    """X v2 search. PAID: ~$0.005/post returned."""
    token = ENV.get("X_BEARER_TOKEN")
    if not token:
        sys.exit("X_BEARER_TOKEN missing from research/.env")
    endpoint = "tweets/search/all" if archive else "tweets/search/recent"
    params = {"query": query, "max_results": min(max_results, 100),
              "tweet.fields": "public_metrics,created_at,author_id",
              "expansions": "author_id", "user.fields": "username,public_metrics"}
    if archive:
        params["start_time"] = f"{start}T00:00:00Z"
        params["sort_order"] = "relevancy"
    d = http_json(f"https://api.x.com/2/{endpoint}?{urllib.parse.urlencode(params)}",
                  {"Authorization": f"Bearer {token}"})
    users = {u["id"]: u for u in d.get("includes", {}).get("users", [])}
    out = []
    for t in d.get("data", []):
        u, m = users.get(t["author_id"], {}), t["public_metrics"]
        out.append({"date": t["created_at"][:10], "user": u.get("username"),
                    "followers": u.get("public_metrics", {}).get("followers_count", 0),
                    "likes": m["like_count"], "rts": m["retweet_count"],
                    "text": t["text"][:280]})
    out.sort(key=lambda x: -(x["likes"] + 2 * x["rts"]))
    return out


def yt_search(query: str, max_results: int = 10) -> list[dict]:
    key = ENV.get("YOUTUBE_API_KEY") or sys.exit("YOUTUBE_API_KEY missing from research/.env")
    s = http_json("https://www.googleapis.com/youtube/v3/search?" + urllib.parse.urlencode(
        {"part": "snippet", "q": query, "type": "video", "maxResults": max_results,
         "order": "relevance", "key": key}))
    ids = [i["id"]["videoId"] for i in s.get("items", [])]
    if not ids:
        return []
    stats = http_json("https://www.googleapis.com/youtube/v3/videos?" + urllib.parse.urlencode(
        {"part": "statistics,snippet", "id": ",".join(ids), "key": key}))
    vids = [{"id": v["id"], "title": v["snippet"]["title"], "channel": v["snippet"]["channelTitle"],
             "published": v["snippet"]["publishedAt"][:10],
             "views": int(v["statistics"].get("viewCount", 0)),
             "comments": int(v["statistics"].get("commentCount", 0))} for v in stats.get("items", [])]
    return sorted(vids, key=lambda v: -v["views"])


PAIN_RE = re.compile(r"wish|annoy|expensive|subscript|price|crash|slow|frustrat|hard to|confus"
                     r"|clunky|alternative|switch|problem|can't|cannot|lost my|is there a|how do i", re.I)

def yt_comments(video_id: str, max_comments: int = 200, pain_only: bool = True) -> list[dict]:
    key = ENV.get("YOUTUBE_API_KEY") or sys.exit("YOUTUBE_API_KEY missing from research/.env")
    out, page = [], None
    while len(out) < max_comments:
        params = {"part": "snippet", "videoId": video_id, "maxResults": 100,
                  "order": "relevance", "textFormat": "plainText", "key": key}
        if page:
            params["pageToken"] = page
        d = http_json("https://www.googleapis.com/youtube/v3/commentThreads?" + urllib.parse.urlencode(params))
        for item in d.get("items", []):
            sn = item["snippet"]["topLevelComment"]["snippet"]
            out.append({"likes": sn["likeCount"], "text": sn["textDisplay"][:300]})
        page = d.get("nextPageToken")
        if not page:
            break
    if pain_only:
        out = [c for c in out if PAIN_RE.search(c["text"])]
    return sorted(out, key=lambda c: -c["likes"])


def steam(name_or_appid: str) -> dict:
    if name_or_appid.isdigit():
        appid = int(name_or_appid)
    else:
        d = http_json("https://store.steampowered.com/api/storesearch/?" + urllib.parse.urlencode(
            {"term": name_or_appid, "cc": "us", "l": "en"}))
        if not d.get("items"):
            return {"error": f"no steam app found for {name_or_appid!r}"}
        appid = d["items"][0]["id"]
    spy = http_json(f"https://steamspy.com/api.php?request=appdetails&appid={appid}")
    rev = http_json(f"https://store.steampowered.com/appreviews/{appid}?json=1&num_per_page=0&l=en")
    q = rev.get("query_summary", {})
    return {"appid": appid, "name": spy.get("name"), "owners_est": spy.get("owners"),
            "price_cents": spy.get("price"), "reviews_total": q.get("total_reviews"),
            "reviews_positive": q.get("total_positive"), "score": q.get("review_score_desc")}


def hn(query: str, max_items: int = 10) -> list[dict]:
    d = http_json("https://hn.algolia.com/api/v1/search?" + urllib.parse.urlencode(
        {"query": query, "tags": "story", "hitsPerPage": max_items}))
    return [{"date": h.get("created_at", "")[:10], "points": h.get("points"),
             "comments": h.get("num_comments"), "title": h.get("title"),
             "url": f"https://news.ycombinator.com/item?id={h.get('objectID')}"}
            for h in d.get("hits", [])]

# ---------------------------------------------------------------------- main

def pretty(rows, cols):
    for r in rows:
        print("  " + " | ".join(str(r.get(c, ""))[:100] for c in cols))

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("news"); p.add_argument("query"); p.add_argument("--max", type=int, default=12)
    p = sub.add_parser("trends"); p.add_argument("keywords"); p.add_argument("--timeframe", default="today 5-y")
    p = sub.add_parser("x"); p.add_argument("query"); p.add_argument("--archive", action="store_true")
    p.add_argument("--max", type=int, default=50); p.add_argument("--yes", action="store_true")
    p.add_argument("--start", default="2015-01-01")
    p = sub.add_parser("yt-search"); p.add_argument("query"); p.add_argument("--max", type=int, default=10)
    p = sub.add_parser("yt-comments"); p.add_argument("video_id"); p.add_argument("--max", type=int, default=200)
    p.add_argument("--all-comments", action="store_true")
    p = sub.add_parser("steam"); p.add_argument("name_or_appid")
    p = sub.add_parser("hn"); p.add_argument("query"); p.add_argument("--max", type=int, default=10)
    p = sub.add_parser("all"); p.add_argument("topic")
    a = ap.parse_args()

    if a.cmd == "news":
        data = news(a.query, a.max); pretty(data, ["date", "source", "title"])
    elif a.cmd == "trends":
        data = trends([k.strip() for k in a.keywords.split(",")], a.timeframe)
        print(json.dumps(data, indent=1))
    elif a.cmd == "x":
        cost = a.max * X_COST_PER_POST
        if a.max > 500 and not a.yes:
            sys.exit(f"--max {a.max} would cost ~${cost:.2f}; re-run with --yes to confirm")
        print(f"(estimated cost up to ~${cost:.2f})")
        data = x_search(a.query, a.archive, a.max, a.start)
        pretty(data, ["date", "user", "followers", "likes", "text"])
    elif a.cmd == "yt-search":
        data = yt_search(a.query, a.max); pretty(data, ["views", "comments", "published", "title", "channel"])
    elif a.cmd == "yt-comments":
        data = yt_comments(a.video_id, a.max, pain_only=not a.all_comments)
        pretty(data, ["likes", "text"])
    elif a.cmd == "steam":
        data = steam(a.name_or_appid); print(json.dumps(data, indent=1))
    elif a.cmd == "hn":
        data = hn(a.query, a.max); pretty(data, ["date", "points", "comments", "title", "url"])
    elif a.cmd == "all":
        data = {"topic": a.topic, "news": news(a.topic), "hn": hn(a.topic),
                "yt": yt_search(a.topic), "trends": trends([a.topic])}
        for section in ("news", "hn", "yt"):
            print(f"\n== {section}")
            pretty(data[section], {"news": ["date", "source", "title"],
                                   "hn": ["date", "points", "title"],
                                   "yt": ["views", "published", "title", "channel"]}[section])
        print("\n== trends"); print(json.dumps(data["trends"], indent=1))
    label = next((getattr(a, f) for f in ("query", "topic", "keywords", "video_id", "name_or_appid")
                  if hasattr(a, f)), "")
    print(f"\nsaved: {save(f'{a.cmd}-{label}', data)}")

if __name__ == "__main__":
    main()
