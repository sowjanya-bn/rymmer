#!/usr/bin/env python3
"""RYM Collector — local HTTP server (localhost:7842)

Endpoints:
  POST /collect  — receive JSON from extension, append to ~/.rymmer/rym_collected.json
  GET  /status   — return count of collected records
  GET  /export   — return all collected records as a JSON array
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PORT = 7842
STORE = Path.home() / ".rymmer" / "rym_collected.json"


def load_records():
    if not STORE.exists():
        return []
    records = []
    with STORE.open() as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def known_urls():
    return {r["url"] for r in load_records() if "url" in r}


def append_record(record):
    STORE.parent.mkdir(parents=True, exist_ok=True)
    with STORE.open("a") as f:
        f.write(json.dumps(record) + "\n")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[rym_server] {self.address_string()} - {fmt % args}", file=sys.stderr)

    def send_json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        # Allow requests from the extension content script
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path != "/collect":
            self.send_json(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            record = json.loads(body)
        except json.JSONDecodeError:
            self.send_json(400, {"error": "invalid JSON"})
            return

        url = record.get("url", "")
        if url in known_urls():
            self.send_json(200, {"status": "duplicate", "url": url})
            return

        append_record(record)
        record_type = record.get("type", "album")
        print(f"[rym_server] saved {record_type}: {url}", file=sys.stderr)
        self.send_json(200, {"status": "saved", "url": url})

    def do_GET(self):
        if self.path == "/status":
            records = load_records()
            self.send_json(200, {"count": len(records), "store": str(STORE)})
        elif self.path == "/export":
            records = load_records()
            self.send_json(200, records)
        else:
            self.send_json(404, {"error": "not found"})


def main():
    STORE.parent.mkdir(parents=True, exist_ok=True)
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"[rym_server] Listening on http://127.0.0.1:{PORT}")
    print(f"[rym_server] Storing to {STORE}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[rym_server] Stopped.")


if __name__ == "__main__":
    main()
