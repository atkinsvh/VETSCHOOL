# Veterinary anatomy model library

Drop downloaded `.glb` files into species folders, for example:

- `assets/models/dog/`
- `assets/models/cat/`
- `assets/models/horse/`
- `assets/models/pig/`
- `assets/models/cow/`

The app serves runtime models from `public/models/...`. Use `scripts/download_glb_assets.py` to download direct GLB URLs into `public/models` and keep `assets/metadata/models.json` in sync.
