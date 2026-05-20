#!/usr/bin/env python3
"""Download GLB assets listed in assets/metadata/models.json.

Usage:
  python scripts/download_glb_assets.py --id dog_skeleton_001 --url https://.../file.glb
  python scripts/download_glb_assets.py --manifest assets/metadata/models.json --download-ready
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DEFAULT = ROOT / "assets" / "metadata" / "models.json"
PUBLIC_MODELS = ROOT / "public" / "models"


def load_manifest(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(path: Path, models: list[dict]) -> None:
    path.write_text(json.dumps(models, indent=2) + "\n", encoding="utf-8")


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url) as response:  # nosec - controlled by operator input
        data = response.read()
    destination.write_bytes(data)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST_DEFAULT)
    parser.add_argument("--id", help="Model id to update")
    parser.add_argument("--url", help="Direct .glb URL for --id")
    parser.add_argument("--download-ready", action="store_true", help="Download entries with download_status=ready")
    args = parser.parse_args()

    models = load_manifest(args.manifest)
    by_id = {m["id"]: m for m in models}

    if args.id and args.url:
        model = by_id[args.id]
        local_rel = model["local_glb_path"].removeprefix("/models/")
        target = PUBLIC_MODELS / local_rel
        download(args.url, target)
        model["source_url"] = args.url
        model["download_status"] = "downloaded"
        model["mode"] = "local"
        save_manifest(args.manifest, models)
        print(f"Downloaded {args.id} -> {target}")
        return

    if args.download_ready:
        for model in models:
            if model.get("download_status") == "ready" and model.get("source_url", "").endswith(".glb"):
                local_rel = model["local_glb_path"].removeprefix("/models/")
                target = PUBLIC_MODELS / local_rel
                download(model["source_url"], target)
                model["download_status"] = "downloaded"
                model["mode"] = "local"
                print(f"Downloaded {model['id']}")
        save_manifest(args.manifest, models)
        return

    parser.error("Provide --id/--url or --download-ready")


if __name__ == "__main__":
    main()
