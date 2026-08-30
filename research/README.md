# Research Pipeline

One CLI over every market-research data source used for vMap PMF work. Results print to terminal and save as JSON under `research/out/` (gitignored).

## Setup

Keys live in `research/.env` (gitignored):

```
X_BEARER_TOKEN=...      # X/Twitter v2 API (paid per post on search)
YOUTUBE_API_KEY=...     # YouTube Data API v3 (free, 10k units/day)
```

Google Trends needs pytrends: `python3 -m venv .venv && .venv/bin/pip install pytrends`, then run trends commands with `.venv/bin/python`. Everything else is stdlib.

## Commands

| Command | Source | Cost |
|---|---|---|
| `pipeline.py news "query"` | Google News hidden RSS | free |
| `pipeline.py trends "kw1,kw2"` | Google Trends (pytrends; retries through 429s) | free |
| `pipeline.py x "query" [--archive] [--max N]` | X v2 search (recent = 7 days; `--archive` = back to 2006) | **~$0.005/post** — prints estimate, refuses >500 without `--yes` |
| `pipeline.py yt-search "query"` | YouTube search + view/comment counts | free |
| `pipeline.py yt-comments VIDEO_ID` | Top comments, filtered to pain/wish language (`--all-comments` to disable) | free |
| `pipeline.py steam "name or appid"` | SteamSpy owners estimate + Steam review counts | free |
| `pipeline.py hn "query"` | Hacker News (Algolia) | free |
| `pipeline.py all "topic"` | news + hn + yt + trends in one shot | free |

## X query tips

Full-archive supports operators: `("phrase" OR word) -is:retweet lang:en`, `sort_order=relevancy` is applied automatically, `--start YYYY-MM-DD` sets the window. High-signal patterns used so far: tool name + `(wish OR expensive OR alternative OR lost)`, `"wish there was"` + category words, concept phrases like `"google maps" ("middle earth" OR "fictional world")`.

## Findings live elsewhere

Raw pulls land in `out/`; synthesized findings belong in `private/market research - pmf and first 100 users.md` and links in `private/research links.md`.
