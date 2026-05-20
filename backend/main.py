from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path
from typing import Any
from collections import OrderedDict

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


def humanize(value: str) -> str:
    return value.replace("_", " ").strip().title()


def load_species_metadata() -> list[dict]:
    species_path = ASSETS_METADATA_DIR / "species.json"
    if species_path.exists():
        return json.loads(species_path.read_text(encoding="utf-8"))
    structures = load_json("structures.json")
    return [{"id": key, "label": key.title()} for key in structures.keys()]


def load_system_metadata() -> list[dict]:
    systems_path = ASSETS_METADATA_DIR / "systems.json"
    if systems_path.exists():
        return json.loads(systems_path.read_text(encoding="utf-8"))
    return []


def normalize_model_record(item: dict, *, asset_manifest: bool) -> dict:
    return {
        "id": item["id"],
        "title": item.get("model_name" if asset_manifest else "title", item["id"]),
        "species": item["species"],
        "system": item.get("anatomy_system" if asset_manifest else "system", "unknown"),
        "source": item.get("source", ""),
        "source_url": item.get("source_url"),
        "local_file": item.get("local_glb_path" if asset_manifest else "local_file"),
        "mode": item.get("mode", "external_until_downloaded"),
        "notes": item.get("license_usage_notes" if asset_manifest else "notes", ""),
        "tags": item.get("tags", []),
        "download_status": item.get("download_status", "external_only"),
        "clickable_nodes": item.get("clickable_nodes", []),
    }


def load_registry_models() -> list[dict]:
    registry_path = ASSETS_METADATA_DIR / "models.json"
    if not registry_path.exists():
        return [normalize_model_record(item, asset_manifest=False) for item in load_json("models.json")]

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    return [normalize_model_record(item, asset_manifest=True) for item in registry]


def build_chapters() -> list[dict]:
    models = load_registry_models()
    quizzes = load_json("quizzes.json")
    structures = load_json("structures.json")
    species_lookup = {item["id"]: item for item in load_species_metadata()}
    system_lookup = {item["id"]: item for item in load_system_metadata()}

    grouped: OrderedDict[tuple[str, str], list[dict]] = OrderedDict()
    for model in models:
        key = (model["species"], model["system"])
        grouped.setdefault(key, []).append(model)

    chapters: list[dict] = []
    for index, ((species, system), chapter_models) in enumerate(grouped.items(), start=1):
        species_label = species_lookup.get(species, {}).get("label", humanize(species))
        system_label = system_lookup.get(system, {}).get("label", humanize(system))
        quiz_items = quizzes.get(species, {}).get(system, [])
        structure_items = structures.get(species, {}).get(system, {})
        local_models = [item for item in chapter_models if item.get("mode") == "local"]
        external_models = [item for item in chapter_models if item.get("mode") != "local"]
        chapter_id = f"{species}--{system}"

        chapters.append({
            "id": chapter_id,
            "chapter_number": index,
            "title": f"{species_label} {system_label}",
            "eyebrow": f"Chapter {index:02d}",
            "species": species,
            "species_label": species_label,
            "system": system,
            "system_label": system_label,
            "summary": (
                f"Study {len(chapter_models)} model source"
                f"{'' if len(chapter_models) == 1 else 's'} for {species_label.lower()} {system_label.lower()}, "
                f"inspect {len(structure_items)} mapped structure"
                f"{'' if len(structure_items) == 1 else 's'}, and work through {len(quiz_items)} quiz prompt"
                f"{'' if len(quiz_items) == 1 else 's'}."
            ),
            "goals": [
                f"Review the {system_label.lower()} forms available for {species_label.lower()}.",
                "Open a model, inspect a mesh or placeholder node, and connect it to anatomy notes.",
                "Use the quiz panel to turn each chapter into a study session."
            ],
            "stats": {
                "model_count": len(chapter_models),
                "local_model_count": len(local_models),
                "external_model_count": len(external_models),
                "quiz_count": len(quiz_items),
                "structure_count": len(structure_items),
            },
            "models": chapter_models,
        })

    return chapters

@app.get("/")
def root():
    return {"status": "online", "project": "BioAtlas Vet", "phase": 3, "docs": "/docs"}

@app.get("/api/species")
def species():
    return load_species_metadata()

@app.get("/api/models")
def models():
    return load_registry_models()


@app.get("/api/chapters")
def chapters():
    return build_chapters()

@app.get("/api/models/{species}/{system}")
def model(species: str, system: str):
    matches = [m for m in load_registry_models() if m["species"] == species and m["system"] == system]
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
