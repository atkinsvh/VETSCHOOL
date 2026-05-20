#!/usr/bin/env python3
"""Hybrid scraper+API: scrape Sketchfab search pages for model UIDs, then query API for .glb URLs.

Usage: python scripts/hybrid_scrape_api_glb.py --token <TOKEN>

Limits to first 100 manifest entries.
Writes discovered mappings to `assets/metadata/model_urls_hybrid.json`.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Optional

import requests

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "metadata" / "models.json"
OUT = ROOT / "assets" / "metadata" / "model_urls_hybrid.json"


def search_sketchfab_api(token: str, query: str) -> list[str]:
    """Search Sketchfab via the API (not scraping) and extract model UIDs."""
    headers = {"Authorization": f"Token {token}"}
    params = {
        "type": "models",
        "q": query,
        "count": 5,
        "downloadable": "true"
    }
    try:
        r = requests.get("https://api.sketchfab.com/v3/search", headers=headers, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        
        uids = []
        for result in results:
            uid = result.get("uid") or result.get("id")
            if uid:
                uids.append(uid)
        
        return uids
    except Exception as e:
        print(f"  api search error: {e}")
        return []


def get_model_download_info(token: str, uid: str) -> Optional[dict]:
    """Query Sketchfab API for a model's download endpoint."""
    headers = {"Authorization": f"Token {token}"}
    try:
        r = requests.get(f"https://api.sketchfab.com/v3/models/{uid}/download", 
                        headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def find_glb_url(info: dict) -> Optional[str]:
    """Recursively search for .glb URLs in download info."""
    def scan(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                r = scan(v)
                if r:
                    return r
        elif isinstance(obj, list):
            for v in obj:
                r = scan(v)
                if r:
                    return r
        elif isinstance(obj, str):
            if ".glb" in obj.lower() and obj.lower().split("?", 1)[0].endswith(".glb"):
                return obj
        return None
    
    return scan(info) if info else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True, help="Sketchfab API token")
    parser.add_argument("--limit", type=int, default=100, help="Max manifest entries to process")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mapping: dict[str, str] = {}

    count = 0
    for item in manifest:
        if count >= args.limit:
            break

        mid = item.get("id")
        src = item.get("source_url", "")
        if not mid or not src:
            count += 1
            continue

        # Skip if already a direct .glb
        if src.lower().split("?", 1)[0].endswith(".glb"):
            count += 1
            continue

        # Skip if not a Sketchfab URL (we'll search by model name instead)
        # Build search query from model_name, species, tags
        parts = []

        if item.get("species"):
            parts.append(item["species"])
        if item.get("tags"):
            parts.extend(item["tags"][:2])
        
        query = " ".join(parts).strip()
        if not query:
            count += 1
            continue

        print(f"Processing {mid}: searching API for '{query}'")
        uids = search_sketchfab_api(args.token, query)
        if not uids:
            print("  no results from API")
            count += 1
            time.sleep(1.0)
            continue

        found = False
        for uid in uids:
            print(f"  checking uid {uid}...")
            info = get_model_download_info(args.token, uid)
            glb_url = find_glb_url(info) if info else None
            if glb_url:
                print(f"  found: {glb_url}")
                mapping[mid] = glb_url
                found = True
                break

        if not found:
            print("  no .glb found in any result")

        count += 1
        time.sleep(1.0)

    if mapping:
        OUT.write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8")
        print(f"\nWROTE {OUT} with {len(mapping)} entries")
    else:
        print("No .glb URLs discovered.")


if __name__ == "__main__":
    main()
