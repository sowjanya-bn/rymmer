# RYM Collector — Browser Extension Spec

## Goal
Passively collect RateYourMusic album data as the user browses normally.
No scraping, no bots, no Cloudflare issues.

## Components

### 1. Chrome Extension
Triggers automatically on any `rateyourmusic.com/release/album/*` page.
Extracts data from the live DOM and POSTs to a local collector server.

**Manifest V3 permissions:**
- `activeTab`
- Host permission: `*://rateyourmusic.com/*`

**Content script triggers on:** `https://rateyourmusic.com/release/album/*/*`

**Data extracted per page:**
```json
{
  "url": "https://rateyourmusic.com/release/album/maren-morris/hero/",
  "title": "HERO",
  "artist": "Maren Morris",
  "year": "2016",
  "genres": ["Country Pop", "Pop Rock", "Pop Soul", "Country Rock"],
  "descriptors": ["female vocalist", "..."],
  "rating": 3.25,
  "ratings_count": 393,
  "rank_year": "1045",
  "rank_year_label": "2016",
  "reviews": [
    { "author": "username", "text": "..." }
  ],
  "collected_at": "2026-07-07T17:00:00Z"
}
```

**DOM selectors (verified against HAR):**
- Rating: `.avg_rating`
- Ratings count: `.num_ratings b span`
- Rank: `td:has(> "Ranked") + td b` (parse from text)
- Genres: `.release_pri_genres a`, `.release_sec_genres a`
- Descriptors: `.release_pri_descriptors` (comma-split text)
- Reviews: `.review .review_header [title^="User"]` + `.review_body`
- Title: `h1.release_page_title` or `<title>` parse
- Artist: `.artist a` or `<title>` parse
- Year: `.issue_year` or release info table

**Behaviour:**
- Runs once per page load
- Shows a small badge/notification: "RYM: saved ✓" or "RYM: already collected"
- Skips if URL already in local DB (dedup by URL)
- Also triggers on artist pages (`/artist/*`) to collect discography metadata

### 2. Local Collector Server (`scripts/rym_server.py`)
Tiny HTTP server, runs on `localhost:7842`.

**Endpoints:**
- `POST /collect` — receives JSON from extension, saves to store
- `GET /status` — returns count of collected albums
- `GET /export` — returns all collected data as JSON

**Storage:** append to `~/.silt/rym_collected.json` (newline-delimited JSON, one record per line)

**Later:** `scripts/rym_import.py` reads `~/.silt/rym_collected.json` and upserts into silt's SQLite DB (`tracks` table — adds `rym_rating`, `rym_rank`, `rym_descriptors` columns).

### 3. Import Script (`scripts/rym_import.py`)
Reads collected JSON, matches against tracks in silt DB by artist+title, upserts RYM metadata.

**DB additions to `tracks` table:**
- `rym_rating REAL`
- `rym_rank TEXT`
- `rym_descriptors TEXT` (comma-separated)
- `rym_genres TEXT` (comma-separated)
- `rym_url TEXT`

## Usage Flow
1. `python3 scripts/rym_server.py` — start collector (or add to cron)
2. Load extension in Chrome (`chrome://extensions` → Load unpacked)
3. Browse RYM naturally — visit artist pages, album pages
4. Data accumulates in `~/.silt/rym_collected.json`
5. Run `python3 scripts/rym_import.py` to sync into silt DB

## Files
```
rym-extension/
  manifest.json
  content.js       # DOM extraction + POST to local server
  background.js    # (optional) badge management
  icon.png
scripts/
  rym_server.py    # local collector HTTP server
  rym_import.py    # import collected JSON into silt DB
```

## Non-goals
- No login/auth handling — user is already logged in
- No active navigation — passive collection only
- No rate limiting needed — user controls browse speed
