#!/usr/bin/env python3
"""rym_browse.py — automate RYM browsing to trigger passive collection.

Uses your existing Chrome profile (already logged in, extension active).

Usage:
  python3 scripts/rym_browse.py https://rateyourmusic.com/release/album/maren-morris/hero/
  python3 scripts/rym_browse.py --file urls.txt

For each URL, parses artist + album slugs, then:
  1. Goes to rateyourmusic.com home
  2. Searches for the artist
  3. Finds the album in discography and clicks it
  4. Waits for extension to collect, then moves on
"""

import random
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

CHROME_PROFILE = "/Users/sowjanya/Library/Application Support/Google/Chrome"
RYM = "https://rateyourmusic.com"


def pause(lo=8, hi=18):
    time.sleep(random.uniform(lo, hi))


def parse_url(url):
    """Return (artist_slug, album_slug) from a RYM album URL."""
    parts = urlparse(url).path.strip("/").split("/")
    # release/album/<artist>/<album>
    if len(parts) >= 4:
        return parts[2], parts[3]
    return None, None


def slug_to_name(slug):
    """Convert 'maren-morris' -> 'Maren Morris' for search."""
    return slug.replace("-", " ").title()


def collect_album(page, url):
    artist_slug, album_slug = parse_url(url)
    if not artist_slug:
        print(f"  could not parse URL: {url}")
        return

    artist_name = slug_to_name(artist_slug)
    album_name = slug_to_name(album_slug)
    print(f"\n[rym_browse] {artist_name} — {album_name}")

    # Search from home page
    page.goto(RYM, wait_until="domcontentloaded")
    print(f"  on page: {page.url}")
    pause(3, 6)
    page.fill("#ui_search_input_main_search", artist_name)
    page.keyboard.press("Enter")
    pause(3, 6)

    # Click first artist result
    artist_link = page.locator(f"a[href*='/artist/{artist_slug}']").first
    if not artist_link.is_visible():
        print(f"  artist not found: {artist_name}")
        return
    artist_link.click()
    pause(3, 6)

    # Type album name into discography filter, then click the first result
    disco_search = page.locator("#disco_search")
    disco_search.wait_for(state="visible", timeout=10000)
    disco_search.click()
    disco_search.type(album_name, delay=80)
    pause(1, 2)

    album_link = page.locator("div.disco_release:visible a.album").first
    if not album_link.is_visible():
        print(f"  album not found: {album_name}")
        return

    album_link.click()
    pause(12, 20)  # let the extension collect
    print(f"  collected.")


def load_urls(args):
    urls = []
    i = 0
    while i < len(args):
        if args[i] == "--file":
            i += 1
            for line in Path(args[i]).read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)
        else:
            urls.append(args[i])
        i += 1
    return urls


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    urls = load_urls(sys.argv[1:])
    print(f"[rym_browse] {len(urls)} album(s) to collect")

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        # Use existing RYM page if open, otherwise open a new one
        pages = context.pages
        rym_pages = [p for p in pages if "rateyourmusic.com" in p.url]
        page = rym_pages[0] if rym_pages else context.new_page()
        print(f"[rym_browse] connected to Chrome (using page: {page.url})")

        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}]")
            collect_album(page, url)
            if i < len(urls):
                pause(5, 10)

        page.close()
    print("\n[rym_browse] all done.")


if __name__ == "__main__":
    main()
