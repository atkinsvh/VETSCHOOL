import { useEffect, useState } from "react";
import { api } from "./lib/api.js";
import AnatomyViewer from "./components/AnatomyViewer.jsx";
import InfoPanel from "./components/InfoPanel.jsx";
import QuizEngine from "./components/QuizEngine.jsx";
import ModelRegistry from "./components/ModelRegistry.jsx";

export default function App() {
  const [models, setModels] = useState([]);
  const [activeModel, setActiveModel] = useState(null);
  const [selectedStructure, setSelectedStructure] = useState(null);
  const [selectedMeshName, setSelectedMeshName] = useState("");

  useEffect(() => {
    api.models().then((items) => {
      setModels(items);
      setActiveModel(items[0] || null);
    });
  }, []);

  async function handleStructureClick(id, meshName = "") {
    setSelectedMeshName(meshName || id);
    if (!activeModel) return;
    try {
      const data = await api.structure(activeModel.species, activeModel.system, id);
      setSelectedStructure(data);
    } catch {
      setSelectedStructure({
        id,
        name: id,
        system: activeModel.system,
        region: "Unmapped",
        function: "This mesh/node is not mapped yet. Add it to backend/data/structures.json.",
        attachments: [],
        clinical_notes: [],
        study_prompt: "Map this node to a structure and write a study prompt."
      });
    }
  }

  return (
    <main className="app-shell">
      <section className="main-column">
        <header className="hero">
          <p className="eyebrow">BioAtlas Vet · Phase 3</p>
          <h1>Sketchfab-ready 3D veterinary anatomy atlas</h1>
          <p>Drop legal GLB files into <code>public/models</code>, inspect mesh names, map anatomy IDs, and study with quizzes.</p>
        </header>

        <ModelRegistry
          models={models}
          activeModel={activeModel}
          onSelect={setActiveModel}
        />

        <AnatomyViewer
          model={activeModel}
          selectedId={selectedStructure?.id}
          onStructureClick={handleStructureClick}
        />
      </section>

      <aside className="side-column">
        <InfoPanel structure={selectedStructure} meshName={selectedMeshName} model={activeModel} />
        <QuizEngine species={activeModel?.species} system={activeModel?.system} />
      </aside>
    </main>
  );
}
