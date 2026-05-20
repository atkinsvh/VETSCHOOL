# BioAtlas Vet — Phase 3 Sketchfab-Ready Build

This ZIP is prepared for the vetanatMunich Sketchfab models, but it does **not** include copied Sketchfab model files because the public gallery/model pages do not expose a direct downloadable `.glb` URL from this environment.

## What this build adds

- BioAtlas Vet branding
- Real `.glb/.gltf` model loader with fallback placeholders
- Sketchfab external model registry entries
- Model source links
- Node-name inspector
- Clickable placeholder anatomy
- API metadata lookup
- Species/model selector
- Quiz engine
- Drop-zone folder for real downloaded models

## Manual model install

1. Open the model source from the app or registry.
2. Download the model from Sketchfab if your account/license allows it.
3. If Sketchfab gives you `.obj` or `.fbx`, convert it to `.glb` in Blender.
4. Place the file here:

```txt
public/models/pig_skeleton.glb
```

5. Run the app. The model registry already points to:

```txt
/models/pig_skeleton.glb
```

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

## API routes

```txt
GET /api/species
GET /api/models
GET /api/models/{species}/{system}
GET /api/structures/{species}/{system}/{structure_id}
GET /api/quizzes/{species}/{system}
```
