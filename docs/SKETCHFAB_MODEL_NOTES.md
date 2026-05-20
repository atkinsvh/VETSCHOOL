# Sketchfab / vetanatMunich Notes

The vetanatMunich profile has hundreds of public veterinary anatomy models. This app is configured to reference them as source URLs and to load local GLB copies after you download them manually.

## Important

Do not redistribute models unless the license allows it. For private friend/study use, downloading through your own Sketchfab account may be fine depending on the model license, but the ZIP itself should avoid bundling restricted assets unless you are sure.

## First target

Skeleton of a Pig:
https://sketchfab.com/3d-models/skeleton-of-a-pig-044c0b61e2e24d04a08b9fbd8de3c163

Expected local path:
public/models/pig_skeleton.glb

## Blender conversion

If downloaded as OBJ/FBX:

1. Open Blender
2. File > Import > OBJ or FBX
3. File > Export > glTF 2.0
4. Choose GLB binary
5. Name it pig_skeleton.glb
6. Move it into public/models/
