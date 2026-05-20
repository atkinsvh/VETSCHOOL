import { Suspense, useMemo, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Text, useGLTF } from "@react-three/drei";

const positions = {
  femur: [-1.6, 0.7, 0],
  tibia: [-1.6, -0.8, 0],
  radius: [1.6, 0.2, 0],
  ulna: [1.6, -0.9, 0],
  skull: [0, 1.45, 0],
  vertebrae: [0, 0.15, 0]
};

function PlaceholderNode({ id, selected, onClick }) {
  const position = positions[id] || [0, 0, 0];

  return (
    <group position={position}>
      <mesh onClick={(event) => { event.stopPropagation(); onClick(id, id); }}>
        <sphereGeometry args={[selected ? 0.42 : 0.33, 32, 32]} />
        <meshStandardMaterial roughness={0.4} />
      </mesh>
      <Text position={[0, -0.62, 0]} fontSize={0.17} anchorX="center">
        {id}
      </Text>
    </group>
  );
}

function GLBModel({ file, onStructureClick }) {
  const gltf = useGLTF(file);
  const [hovered, setHovered] = useState("");

  const scene = useMemo(() => {
    const cloned = gltf.scene.clone(true);
    cloned.traverse((child) => {
      if (child.isMesh) {
        child.castShadow = true;
        child.receiveShadow = true;
        child.userData.originalName = child.name;
      }
    });
    return cloned;
  }, [gltf]);

  return (
    <primitive
      object={scene}
      scale={1}
      onPointerOver={(event) => {
        event.stopPropagation();
        setHovered(event.object.name);
        document.body.style.cursor = "pointer";
      }}
      onPointerOut={() => {
        setHovered("");
        document.body.style.cursor = "default";
      }}
      onClick={(event) => {
        event.stopPropagation();
        const meshName = event.object.name || "unnamed_mesh";
        const guessedId = meshName.toLowerCase().replaceAll(" ", "_");
        onStructureClick(guessedId, meshName);
      }}
    />
  );
}

export default function AnatomyViewer({ model, selectedId, onStructureClick }) {
  const hasLocalGLB = model?.local_file && model?.mode !== "placeholder";

  return (
    <section className="viewer-card">
      <div className="viewer-meta">
        <strong>{model?.title || "No model"}</strong>
        <span>{hasLocalGLB ? `Trying ${model.local_file}` : "Placeholder mode"}</span>
      </div>

      <Canvas camera={{ position: [0, 1.8, 5], fov: 50 }} shadows>
        <ambientLight intensity={0.75} />
        <directionalLight position={[5, 5, 5]} intensity={1.5} castShadow />
        <gridHelper args={[7, 7]} />

        <Suspense fallback={null}>
          {hasLocalGLB ? (
            <GLBModel file={model.local_file} onStructureClick={onStructureClick} />
          ) : (
            (model?.clickable_nodes || []).map((id) => (
              <PlaceholderNode
                key={id}
                id={id}
                selected={selectedId === id}
                onClick={onStructureClick}
              />
            ))
          )}
        </Suspense>

        {!hasLocalGLB && (model?.clickable_nodes || []).length === 0 && (
          <Text fontSize={0.25}>No model nodes registered.</Text>
        )}

        <OrbitControls />
      </Canvas>

      {hasLocalGLB && (
        <div className="warning-note">
          If the GLB is missing, the viewer may show blank. Put the file at <code>public{model.local_file}</code>.
        </div>
      )}
    </section>
  );
}
