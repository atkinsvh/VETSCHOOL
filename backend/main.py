from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path
from typing import Any

app = FastAPI(title="BioAtlas Vet API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent / "data"
ASSETS_METADATA_DIR = Path(__file__).parent.parent / "assets" / "metadata"

def load_json(filename: str) -> Any:
    with (DATA_DIR / filename).open("r", encoding="utf-8") as file:
        return json.load(file)

@app.get("/")
def root():
    return {"status": "online", "project": "BioAtlas Vet", "phase": 3, "docs": "/docs"}

@app.get("/api/species")
def species():
    species_path = ASSETS_METADATA_DIR / "species.json"
    if species_path.exists():
        return json.loads(species_path.read_text(encoding="utf-8"))
    structures = load_json("structures.json")
    return [{"id": key, "label": key.title()} for key in structures.keys()]

@app.get("/api/models")
def _load_registry_models() -> list[dict]:
    registry_path = ASSETS_METADATA_DIR / "models.json"
    if not registry_path.exists():
        return load_json("models.json")

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    transformed = []
    for item in registry:
        transformed.append({
            "id": item["id"],
            "title": item.get("model_name", item["id"]),
            "species": item["species"],
            "system": item.get("anatomy_system", "unknown"),
            "source": item.get("source", ""),
            "source_url": item.get("source_url"),
            "local_file": item.get("local_glb_path"),
            "mode": item.get("mode", "external_until_downloaded"),
            "notes": item.get("license_usage_notes", ""),
            "tags": item.get("tags", []),
            "download_status": item.get("download_status", "external_only"),
            "clickable_nodes": item.get("clickable_nodes", []),
        })
    return transformed

def models():
    return _load_registry_models()

@app.get("/api/models/{species}/{system}")
def model(species: str, system: str):
    matches = [m for m in _load_registry_models() if m["species"] == species and m["system"] == system]
    if not matches:
        raise HTTPException(status_code=404, detail="No model registered for this species/system")
    return matches[0]

@app.get("/api/structures/{species}/{system}/{structure_id}")
def structure(species: str, system: str, structure_id: str):
    structures = load_json("structures.json")
    try:
        return structures[species][system][structure_id]
    except KeyError:
        raise HTTPException(status_code=404, detail="Structure not found")

@app.get("/api/quizzes/{species}/{system}")
def quiz(species: str, system: str):
    quizzes = load_json("quizzes.json")
    return quizzes.get(species, {}).get(system, [])
