#!/usr/bin/env python3
"""Find direct .glb URLs for manifest entries using DuckDuckGo search results.

This is a best-effort scraper: it queries DuckDuckGo's HTML search and looks
for URLs ending in .glb. It saves any found URLs to
`assets/metadata/model_urls_found.json` for use with the batch downloader.

Usage: python scripts/find_direct_glb_urls.py
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "metadata" / "models.json"
OUT = ROOT / "assets" / "metadata" / "model_urls_found.json"


def ddg_search(query: str) -> str | None:
    url = "https://duckduckgo.com/html/"
    req = Request(url + "?" + f"q={query}", headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(req, timeout=15) as r:
            return r.read().decode("utf-8", errors="ignore")
    except (HTTPError, URLError, TimeoutError) as e:
        print("SEARCH FAIL:", query, e)
        return None


GLB_RE = re.compile(r"https?://[^\s'\"]+?\.glb(?:\?[^\s'\"]*)?", re.IGNORECASE)


def find_glb_in_html(html: str) -> list[str]:
    return GLB_RE.findall(html)


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mapping: dict[str, str] = {}

    for item in manifest:
        mid = item.get("id")
        if not mid:
            continue
        # skip if already has a direct .glb source
        src = item.get("source_url", "")
        if src.lower().split("?", 1)[0].endswith(".glb"):
            continue

        terms = []
        if item.get("model_name"):
            terms.append(item["model_name"])
        if item.get("species"):
            terms.append(item["species"])
        if item.get("tags"):
            terms.extend(item["tags"][:3])

        query = "+".join([t.replace(" ", "+") for t in terms])
        if not query:
            continue

        print(f"Searching for {mid}: {query}")
        html = ddg_search(query)
        if not html:
            continue
        candidates = find_glb_in_html(html)
        valid = None
        for c in candidates:
            # quick validation - try to open small range
            try:
                req = Request(c, headers={"User-Agent": "Mozilla/5.0"})
                with urlopen(req, timeout=15) as r:
                    ct = r.headers.get("Content-Type", "")
                    if r.status == 200 and ("model/gltf-binary" in ct or c.lower().endswith(".glb")):
                        valid = c
                        break
            except Exception:
                continue

        if valid:
            print(f"FOUND {mid} -> {valid}")
            mapping[mid] = valid
        else:
            print(f"No direct .glb found for {mid}")

        # be polite
        time.sleep(1.0)

    if mapping:
        OUT.write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8")
        print("WROTE", OUT)
    else:
        print("No .glb URLs found.")


if __name__ == "__main__":
    main()
