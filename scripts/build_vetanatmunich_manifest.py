#!/usr/bin/env python3
"""Build a standard asset manifest from a vetanatMunich registry export.

Usage:
  python scripts/build_vetanatmunich_manifest.py
  python scripts/build_vetanatmunich_manifest.py --token <SKETCHFAB_TOKEN>

If a token is provided, the script enriches each entry with Sketchfab model
details from the public metadata endpoint. It does not store the token.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "scripts" / "vetanatmunich_models_registry_first_page.json"
DEFAULT_OUTPUT = ROOT / "assets" / "metadata" / "vetanatmunich_models_first_page.json"
DEFAULT_MAIN_MANIFEST = ROOT / "assets" / "metadata" / "models.json"
MODEL_URL = "https://api.sketchfab.com/v3/models/{uid}"


def load_registry(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_manifest(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_model_details(token: str, uid: str, timeout: int) -> dict[str, Any] | None:
    headers = {"Authorization": f"Token {token}"}
    try:
        response = requests.get(MODEL_URL.format(uid=uid), headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        print(f"WARN {uid}: {exc}")
        return None


def build_notes(local_glb_path: str | None, api_downloadable: bool) -> str:
    local_hint = local_glb_path or "/models/vetanatmunich/<file>.glb"
    if api_downloadable:
        return (
            "Sketchfab API reports this model as downloadable. Verify license and "
            f"account permissions before downloading or redistributing, then save it as {local_hint}."
        )
    return (
        "Sketchfab API metadata is available, but this model is not downloadable with the current access. "
        f"If you obtain it manually, save it as {local_hint}."
    )


def transform_model(item: dict[str, Any], details: dict[str, Any] | None) -> dict[str, Any]:
    sketchfab_uid = item.get("sketchfab_uid")
    api_downloadable = bool(details.get("isDownloadable")) if details else False
    local_glb_path = item.get("local_glb_path")
    tags = list(item.get("tags") or [])

    return {
        "id": item.get("registry_id"),
        "model_name": (details or {}).get("name") or item.get("title") or item.get("registry_id"),
        "species": item.get("species"),
        "anatomy_system": item.get("system"),
        "source": item.get("source", "Sketchfab / vetanatMunich"),
        "source_url": (details or {}).get("viewerUrl") or item.get("source_url"),
        "embed_url": (details or {}).get("embedUrl") or item.get("embed_url"),
        "sketchfab_uid": sketchfab_uid,
        "local_glb_path": local_glb_path,
        "license_usage_notes": build_notes(local_glb_path, api_downloadable),
        "tags": tags,
        "download_status": "api_downloadable" if api_downloadable else "external_only",
        "mode": "external_until_downloaded",
        "clickable_nodes": [],
        "api_is_downloadable": api_downloadable,
        "api_face_count": (details or {}).get("faceCount"),
        "api_vertex_count": (details or {}).get("vertexCount"),
        "api_animation_count": (details or {}).get("animationCount"),
        "api_created_at": (details or {}).get("createdAt"),
        "api_published_at": (details or {}).get("publishedAt"),
        "api_license": (details or {}).get("license") or None,
        "registry_notes": item.get("notes"),
    }


def merge_models(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {item["id"]: item for item in incoming if item.get("id")}
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in existing:
        item_id = item.get("id")
        if item_id in by_id:
            merged.append(by_id[item_id])
            seen.add(item_id)
        else:
            merged.append(item)
            if item_id:
                seen.add(item_id)

    for item in incoming:
        item_id = item.get("id")
        if item_id and item_id not in seen:
            merged.append(item)
            seen.add(item_id)

    return merged


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Path to the vetanatMunich registry JSON")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Path to write the standard manifest JSON")
    parser.add_argument(
        "--merge-main-manifest",
        action="store_true",
        help="Also merge the generated vetanatMunich entries into assets/metadata/models.json",
    )
    parser.add_argument(
        "--main-manifest",
        type=Path,
        default=DEFAULT_MAIN_MANIFEST,
        help="Primary app manifest to update when --merge-main-manifest is set",
    )
    parser.add_argument("--token", help="Sketchfab API token. Falls back to SKETCHFAB_TOKEN")
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout in seconds")
    parser.add_argument("--sleep", type=float, default=0.25, help="Delay between API calls in seconds")
    args = parser.parse_args()

    token = args.token or os.environ.get("SKETCHFAB_TOKEN")
    registry = load_registry(args.input)
    models = registry.get("models", [])

    transformed: list[dict[str, Any]] = []
    enriched = 0
    downloadable = 0

    for item in models:
        details = None
        uid = item.get("sketchfab_uid")
        if token and uid:
            details = fetch_model_details(token, uid, args.timeout)
            if details:
                enriched += 1
                if details.get("isDownloadable"):
                    downloadable += 1
            time.sleep(args.sleep)

        transformed.append(transform_model(item, details))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(transformed, indent=2) + "\n", encoding="utf-8")

    print(f"WROTE {args.output}")
    print(f"total={len(transformed)} enriched={enriched} api_downloadable={downloadable}")

    if args.merge_main_manifest:
        existing = load_manifest(args.main_manifest)
        merged = merge_models(existing, transformed)
        args.main_manifest.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
        print(f"MERGED {len(transformed)} vetanatMunich entries into {args.main_manifest}")
        print(f"main_manifest_total={len(merged)}")


if __name__ == "__main__":
    main()
