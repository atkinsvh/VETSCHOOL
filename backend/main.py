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

def load_json(filename: str) -> Any:
    with (DATA_DIR / filename).open("r", encoding="utf-8") as file:
        return json.load(file)

@app.get("/")
def root():
    return {"status": "online", "project": "BioAtlas Vet", "phase": 3, "docs": "/docs"}

@app.get("/api/species")
def species():
    structures = load_json("structures.json")
    return [{"id": key, "label": key.title()} for key in structures.keys()]

@app.get("/api/models")
def models():
    return load_json("models.json")

@app.get("/api/models/{species}/{system}")
def model(species: str, system: str):
    matches = [m for m in load_json("models.json") if m["species"] == species and m["system"] == system]
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
