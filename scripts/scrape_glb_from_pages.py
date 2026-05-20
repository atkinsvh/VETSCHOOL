#!/usr/bin/env python3
"""Scrape manifest source pages for direct .glb links using requests + lxml.

Writes discovered id->url mappings to `assets/metadata/model_urls_scraped.json`.

Usage: python scripts/scrape_glb_from_pages.py
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from lxml import html

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "metadata" / "models.json"
OUT = ROOT / "assets" / "metadata" / "model_urls_scraped.json"

GLB_RE = re.compile(r"https?://[^\s'\"]+?\.glb(?:\?[^\s'\"]*)?", re.IGNORECASE)


def find_glbs_on_page(base_url: str, content: str) -> list[str]:
    tree = html.fromstring(content)
    found = []

    # hrefs and srcs containing .glb (case-insensitive)
    hrefs = tree.xpath("//a[@href]//@href")
    srcs = tree.xpath("//*[@src]//@src")
    for u in hrefs + srcs:
        if u and ".glb" in u.lower():
            found.append(urljoin(base_url, u))

    # fallback: regex search in page text for absolute .glb urls
    for m in GLB_RE.findall(content):
        found.append(m)

    # dedupe while preserving order
    seen = set()
    out = []
    for u in found:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mapping: dict[str, str] = {}

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible)"})

    for item in manifest:
        mid = item.get("id")
        if not mid:
            continue
        src = item.get("source_url", "")
        if not src:
            print(f"SKIP {mid}: no source_url")
            continue
        if src.lower().split("?", 1)[0].endswith(".glb"):
            print(f"SKIP {mid}: already direct .glb")
            continue

        try:
            print(f"GET {mid}: {src}")
            r = session.get(src, timeout=15)
        except Exception as e:
            print(f"ERROR {mid}: {e}")
            continue

        if r.status_code != 200:
            print(f"SKIP {mid}: HTTP {r.status_code}")
            continue

        candidates = find_glbs_on_page(r.url, r.text)
        if candidates:
            mapping[mid] = candidates[0]
            print(f"FOUND {mid} -> {candidates[0]}")
        else:
            print(f"No .glb on page for {mid}")

        time.sleep(0.8)

    if mapping:
        OUT.write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8")
        print("WROTE", OUT)
    else:
        print("No .glb URLs discovered.")


if __name__ == "__main__":
    main()
