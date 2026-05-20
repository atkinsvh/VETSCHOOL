#!/usr/bin/env python3
"""Use Sketchfab API to find direct .glb download URLs for manifest entries.

Usage: python scripts/sketchfab_fetch_glb.py --token <SKETCHFAB_TOKEN>

Limits to the first 100 manifest entries to avoid overuse.
Writes discovered mappings to `assets/metadata/model_urls_sketchfab.json`.
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
OUT = ROOT / "assets" / "metadata" / "model_urls_sketchfab.json"

SEARCH_URL = "https://api.sketchfab.com/v3/search"
MODEL_DOWNLOAD_URL = "https://api.sketchfab.com/v3/models/{uid}/download"


def search_model(token: str, query: str, wider: bool = False, per_page: int = 3) -> list[dict]:
    headers = {"Authorization": f"Token {token}"}
    # use documented 'count' parameter for number of results
    params = {"type": "models", "q": query, "count": per_page}
    if not wider:
        params["downloadable"] = "true"
    try:
        r = requests.get(SEARCH_URL, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        results = data.get("results") or data.get("models") or []
        return results
    except Exception:
        return []


def get_download_info(token: str, uid: str) -> Optional[dict]:
    headers = {"Authorization": f"Token {token}"}
    # try download endpoint first
    try:
        r = requests.get(MODEL_DOWNLOAD_URL.format(uid=uid), headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    # fallback to model details
    try:
        r2 = requests.get(f"https://api.sketchfab.com/v3/models/{uid}", headers=headers, timeout=15)
        r2.raise_for_status()
        return r2.json()
    except Exception:
        return None


def find_glb_from_download_info(info: dict) -> Optional[str]:
    # info may contain keys like 'gltf', 'archives', etc. Look for urls ending with .glb
    if not info:
        return None
    # search string values recursively
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
            if obj.lower().split("?", 1)[0].endswith(".glb"):
                return obj
        return None

    return scan(info)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True, help="Sketchfab API token")
    parser.add_argument("--limit", type=int, default=100, help="Max manifest entries to query")
    parser.add_argument("--wider", action="store_true", help="Allow non-downloadable search results and inspect model details")
    parser.add_argument("--per", type=int, default=3, help="Number of search results to inspect per query when wider")
    args = parser.parse_args()

    token = args.token
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mapping: dict[str, str] = {}

    count = 0
    for item in manifest:
        if count >= args.limit:
            break
        mid = item.get("id")
        if not mid:
            continue
        src = item.get("source_url", "")
        if src.lower().split("?", 1)[0].endswith(".glb"):
            count += 1
            continue

        # build query
        parts = []
        if item.get("model_name"):
            parts.append(item["model_name"])
        if item.get("species"):
            parts.append(item["species"])
        if item.get("tags"):
            parts.extend(item["tags"][:2])
        query = " ".join(parts).strip()
        if not query:
            count += 1
            continue

        print(f"Searching Sketchfab for {mid}: {query}")
        results = search_model(token, query, wider=args.wider, per_page=args.per)
        if not results:
            print("  no result")
            count += 1
            time.sleep(0.5)
            continue

        found_any = False
        for res in results:
            uid = res.get("uid") or res.get("id")
            if not uid:
                continue
            info = get_download_info(token, uid)
            glb = find_glb_from_download_info(info) if info else None
            if glb:
                print(f"  found glb for uid {uid}: {glb}")
                mapping[mid] = glb
                found_any = True
                break

        if not found_any:
            print("  no direct glb in inspected results")

        count += 1
        time.sleep(0.6)

    if mapping:
        OUT.write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8")
        print("WROTE", OUT)
    else:
        print("No .glb URLs discovered via API.")


if __name__ == "__main__":
    main()
