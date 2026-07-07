#!/usr/bin/env python3
"""RYM Import — read ~/.rymmer/rym_collected.json and upsert into rymmer's SQLite DB.

Adds columns to the tracks table:
  rym_rating      REAL
  rym_rank        TEXT
  rym_descriptors TEXT  (comma-separated)
  rym_genres      TEXT  (comma-separated)
  rym_url         TEXT

Matches records by normalised (artist, title) strings.
"""

import json
import re
import sqlite3
import sys
from pathlib import Path

STORE = Path.home() / ".rymmer" / "rym_collected.json"
DB_PATH = Path.home() / ".rymmer" / "rymmer.db"

NEW_COLUMNS = [
    ("rym_rating", "REAL"),
    ("rym_rank", "TEXT"),
    ("rym_descriptors", "TEXT"),
    ("rym_genres", "TEXT"),
    ("rym_url", "TEXT"),
]


def normalise(s):
    if not s:
        return ""
    return re.sub(r"\s+", " ", s.lower().strip())


def ensure_columns(conn):
    existing = {row[1] for row in conn.execute("PRAGMA table_info(tracks)")}
    for col, typ in NEW_COLUMNS:
        if col not in existing:
            conn.execute(f"ALTER TABLE tracks ADD COLUMN {col} {typ}")
            print(f"[rym_import] Added column: {col}")
    conn.commit()


def load_records():
    if not STORE.exists():
        print(f"[rym_import] Store not found: {STORE}", file=sys.stderr)
        return []
    records = []
    with STORE.open() as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    r = json.loads(line)
                    if r.get("type") != "artist":  # skip artist-page records
                        records.append(r)
                except json.JSONDecodeError:
                    pass
    return records


def main():
    if not DB_PATH.exists():
        print(f"[rym_import] DB not found: {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    records = load_records()
    if not records:
        print("[rym_import] No album records to import.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_columns(conn)

    # Build lookup: (norm_artist, norm_title) -> rowid
    track_map = {}
    for row in conn.execute("SELECT rowid, artist, title FROM tracks"):
        key = (normalise(row["artist"]), normalise(row["title"]))
        track_map[key] = row["rowid"]

    updated = 0
    unmatched = 0
    for rec in records:
        key = (normalise(rec.get("artist")), normalise(rec.get("title")))
        rowid = track_map.get(key)
        if rowid is None:
            print(f"[rym_import] no match: {rec.get('artist')} — {rec.get('title')}")
            unmatched += 1
            continue

        conn.execute(
            """UPDATE tracks SET
               rym_rating=?, rym_rank=?, rym_descriptors=?, rym_genres=?, rym_url=?
               WHERE rowid=?""",
            (
                rec.get("rating"),
                rec.get("rank_year"),
                ", ".join(rec.get("descriptors", [])),
                ", ".join(rec.get("genres", [])),
                rec.get("url"),
                rowid,
            ),
        )
        updated += 1

    conn.commit()
    conn.close()
    print(f"[rym_import] Done. Updated: {updated}, Unmatched: {unmatched}")


if __name__ == "__main__":
    main()
