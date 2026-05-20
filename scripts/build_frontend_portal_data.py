#!/usr/bin/env python3
"""Build a standalone frontend data bundle for the chapter portal."""

from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODELS_PATH = ROOT / "assets" / "metadata" / "models.json"
SPECIES_PATH = ROOT / "assets" / "metadata" / "species.json"
SYSTEMS_PATH = ROOT / "assets" / "metadata" / "systems.json"
QUIZZES_PATH = ROOT / "backend" / "data" / "quizzes.json"
STRUCTURES_PATH = ROOT / "backend" / "data" / "structures.json"
OUT_PATH = ROOT / "frontend" / "site-data.js"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def humanize(value: str) -> str:
    return value.replace("_", " ").strip().title()


def build_chapters(
    models: list[dict[str, Any]],
    species_meta: list[dict[str, Any]],
    systems_meta: list[dict[str, Any]],
    quizzes: dict[str, Any],
    structures: dict[str, Any],
) -> list[dict[str, Any]]:
    species_lookup = {item["id"]: item for item in species_meta}
    system_lookup = {item["id"]: item for item in systems_meta}

    grouped: OrderedDict[tuple[str, str], list[dict[str, Any]]] = OrderedDict()
    for model in models:
        key = (model["species"], model.get("anatomy_system", "unknown"))
        grouped.setdefault(key, []).append(model)

    chapters: list[dict[str, Any]] = []
    for index, ((species, system), chapter_models) in enumerate(grouped.items(), start=1):
        species_label = species_lookup.get(species, {}).get("label", humanize(species))
        system_label = system_lookup.get(system, {}).get("label", humanize(system))
        quiz_items = quizzes.get(species, {}).get(system, [])
        structure_items = structures.get(species, {}).get(system, {})
        local_models = [item for item in chapter_models if item.get("mode") == "local"]

        chapters.append({
            "id": f"{species}--{system}",
            "chapter_number": index,
            "eyebrow": f"Chapter {index:02d}",
            "title": f"{species_label} {system_label}",
            "species": species,
            "species_label": species_label,
            "system": system,
            "system_label": system_label,
            "summary": (
                f"Study {len(chapter_models)} lesson model"
                f"{'' if len(chapter_models) == 1 else 's'}, review {len(structure_items)} mapped structure"
                f"{'' if len(structure_items) == 1 else 's'}, and work through {len(quiz_items)} quiz prompt"
                f"{'' if len(quiz_items) == 1 else 's'}."
            ),
            "goals": [
                f"Learn the {system_label.lower()} story for {species_label.lower()}.",
                "Compare available models and open one as the active lesson.",
                "Use the study notes and quiz prompts to turn the chapter into revision material."
            ],
            "stats": {
                "model_count": len(chapter_models),
                "local_model_count": len(local_models),
                "quiz_count": len(quiz_items),
                "structure_count": len(structure_items),
            },
            "models": chapter_models,
        })

    return chapters


def main() -> None:
    models = load_json(MODELS_PATH)
    species_meta = load_json(SPECIES_PATH)
    systems_meta = load_json(SYSTEMS_PATH)
    quizzes = load_json(QUIZZES_PATH)
    structures = load_json(STRUCTURES_PATH)

    bundle = {
        "generated_from": {
            "models": str(MODELS_PATH.relative_to(ROOT)).replace("\\", "/"),
            "species": str(SPECIES_PATH.relative_to(ROOT)).replace("\\", "/"),
            "systems": str(SYSTEMS_PATH.relative_to(ROOT)).replace("\\", "/"),
            "quizzes": str(QUIZZES_PATH.relative_to(ROOT)).replace("\\", "/"),
            "structures": str(STRUCTURES_PATH.relative_to(ROOT)).replace("\\", "/"),
        },
        "models": models,
        "quizzes": quizzes,
        "structures": structures,
        "chapters": build_chapters(models, species_meta, systems_meta, quizzes, structures),
    }

    payload = "window.BIOATLAS_DATA = " + json.dumps(bundle, indent=2) + ";\n"
    OUT_PATH.write_text(payload, encoding="utf-8")
    print(f"WROTE {OUT_PATH}")
    print(f"chapters={len(bundle['chapters'])} models={len(models)}")


if __name__ == "__main__":
    main()
