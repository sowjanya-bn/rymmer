# rymmer

Passively collect RateYourMusic album data as you browse. No scraping, no bots.

## How it works

A Chrome extension extracts album data from RYM pages as you visit them and POSTs it to a local server. Data accumulates in `~/.rymmer/rym_collected.json`.

## Setup

### 1. Start the local server

```bash
python3 scripts/rym_server.py
```

Leave this running in a terminal. It listens on `http://localhost:7842`.

### 2. Load the extension in Chrome

1. Go to `chrome://extensions`
2. Enable **Developer mode** (top right)
3. Click **Load unpacked**
4. Select the `rym-extension/` folder

When prompted, allow the extension to access apps on your device (needed to reach localhost).

### 3. Whitelist localhost in your ad blocker

If you use uBlock Origin, add this to **My filters** to prevent it blocking the local server:

```
@@||localhost:7842^
```

### 4. Browse RYM normally

Visit any album page on `rateyourmusic.com/release/album/...` — a badge will appear in the bottom-right corner confirming the data was saved.

### 5. Export your data

Visit `http://localhost:7842/status` to see how many albums have been collected.

To export all collected data as JSON:

```bash
curl http://localhost:7842/export > rym_export.json
```

### 6. Import into SQLite (optional)

```bash
python3 scripts/rym_import.py
```

Matches collected albums against tracks in `~/.rymmer/rymmer.db` by artist + title and upserts RYM metadata (`rym_rating`, `rym_rank`, `rym_genres`, `rym_descriptors`, `rym_url`).

## Requirements

Python 3.6+ — no pip installs needed (stdlib only).
