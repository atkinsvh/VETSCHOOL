#!/usr/bin/env python3
"""Batch download GLB files for model ids and update manifest.

Input mapping file formats supported:
1) JSON object: {"model_id": "https://...file.glb", ...}
2) JSON list: [{"id": "model_id", "url": "https://...file.glb"}, ...]
3) CSV with headers: id,url

Example:
  python scripts/batch_download_glb_from_list.py \
    --mapping assets/metadata/model_urls.json \
    --manifest assets/metadata/models.json
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DEFAULT = ROOT / "assets" / "metadata" / "models.json"
PUBLIC_MODELS = ROOT / "public" / "models"


def load_manifest(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(path: Path, models: list[dict]) -> None:
    path.write_text(json.dumps(models, indent=2) + "\n", encoding="utf-8")


def parse_mapping(path: Path) -> dict[str, str]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
        if isinstance(data, list):
            out: dict[str, str] = {}
            for item in data:
                if not isinstance(item, dict):
                    raise ValueError("JSON list entries must be objects with id and url")
                model_id = item.get("id")
                url = item.get("url")
                if not model_id or not url:
                    raise ValueError("Each JSON list entry must include id and url")
                out[str(model_id)] = str(url)
            return out
        raise ValueError("JSON mapping must be an object or list of {id, url}")

    if suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or "id" not in reader.fieldnames or "url" not in reader.fieldnames:
                raise ValueError("CSV must have headers: id,url")
            return {str(row["id"]): str(row["url"]) for row in reader if row.get("id") and row.get("url")}

    raise ValueError("Unsupported mapping format. Use .json or .csv")


def ensure_glb_url(url: str) -> bool:
    return url.lower().split("?", 1)[0].endswith(".glb")


def download(url: str, destination: Path, timeout: int = 60) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(url, timeout=timeout) as response:  # nosec - operator-supplied URLs
        data = response.read()
    destination.write_bytes(data)


def iter_selected(mapping: dict[str, str], include_ids: Iterable[str] | None) -> dict[str, str]:
    if not include_ids:
        return mapping
    wanted = set(include_ids)
    return {k: v for k, v in mapping.items() if k in wanted}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mapping", type=Path, required=True, help="Path to JSON/CSV id->url mapping")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_DEFAULT)
    parser.add_argument("--id", action="append", dest="ids", help="Optional id filter (can repeat)")
    parser.add_argument("--strict", action="store_true", help="Fail fast on first error")
    args = parser.parse_args()

    models = load_manifest(args.manifest)
    by_id = {m["id"]: m for m in models}
    mapping = iter_selected(parse_mapping(args.mapping), args.ids)

    ok, failed, skipped = 0, 0, 0

    for model_id, url in mapping.items():
        if model_id not in by_id:
            print(f"SKIP {model_id}: not found in manifest")
            skipped += 1
            continue
        if not ensure_glb_url(url):
            print(f"SKIP {model_id}: URL is not a direct .glb file")
            skipped += 1
            continue

        model = by_id[model_id]
        local_rel = model["local_glb_path"].removeprefix("/models/")
        target = PUBLIC_MODELS / local_rel

        try:
            download(url, target)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            print(f"FAIL {model_id}: {exc}")
            failed += 1
            if args.strict:
                raise
            continue

        model["source_url"] = url
        model["download_status"] = "downloaded"
        model["mode"] = "local"
        ok += 1
        print(f"OK   {model_id} -> {target}")

    save_manifest(args.manifest, models)
    print(f"\nSummary: ok={ok} failed={failed} skipped={skipped} total={len(mapping)}")


if __name__ == "__main__":
    main()
