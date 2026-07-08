#!/usr/bin/env python3
"""rym_open.py — open RYM album URLs in your browser for passive collection.

Usage:
  python3 scripts/rym_open.py <url> [url2] [url3] ...
  python3 scripts/rym_open.py --file urls.txt

For each album URL, opens:
  1. The artist page  (so the extension collects discography metadata)
  2. The album page   (so the extension collects full album data)

Waits 10-20 seconds between each page open (randomised to avoid patterns).
"""

import random
import sys
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlparse


def artist_url_from_album_url(album_url):
    """Extract artist slug from album URL and return artist page URL.

    e.g. https://rateyourmusic.com/release/album/maren-morris/hero/
      -> https://rateyourmusic.com/artist/maren-morris/
    """
    parts = urlparse(album_url).path.strip("/").split("/")
    # path: release/album/<artist-slug>/<album-slug>
    if len(parts) >= 4 and parts[0] == "release" and parts[1] == "album":
        artist_slug = parts[2]
        return f"https://rateyourmusic.com/artist/{artist_slug}/"
    return None


def load_urls(args):
    urls = []
    i = 0
    while i < len(args):
        if args[i] == "--file":
            i += 1
            path = Path(args[i])
            for line in path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)
        else:
            urls.append(args[i])
        i += 1
    return urls


def wait(label):
    delay = random.randint(10, 20)
    print(f"  waiting {delay}s before {label}...")
    time.sleep(delay)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    urls = load_urls(sys.argv[1:])
    print(f"[rym_open] {len(urls)} album(s) to collect\n")

    for i, album_url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {album_url}")

        artist_url = artist_url_from_album_url(album_url)
        if artist_url:
            print(f"  → opening artist page: {artist_url}")
            webbrowser.open(artist_url)
            wait("album page")

        print(f"  → opening album page:  {album_url}")
        webbrowser.open(album_url)

        if i < len(urls):
            wait(f"next album ({i+1}/{len(urls)})")

    print("\n[rym_open] done.")


if __name__ == "__main__":
    main()
