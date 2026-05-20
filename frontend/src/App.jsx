import { useEffect, useState } from "react";
import { api } from "./lib/api.js";
import ChapterNavigator from "./components/ChapterNavigator.jsx";
import AnatomyViewer from "./components/AnatomyViewer.jsx";
import InfoPanel from "./components/InfoPanel.jsx";
import QuizEngine from "./components/QuizEngine.jsx";
import ModelRegistry from "./components/ModelRegistry.jsx";

export default function App() {
  const [chapters, setChapters] = useState([]);
  const [activeChapter, setActiveChapter] = useState(null);
  const [activeModel, setActiveModel] = useState(null);
  const [selectedStructure, setSelectedStructure] = useState(null);
  const [selectedMeshName, setSelectedMeshName] = useState("");

  useEffect(() => {
    api.chapters().then((items) => {
      setChapters(items);
      const firstChapter = items[0] || null;
      setActiveChapter(firstChapter);
      setActiveModel(firstChapter?.models?.[0] || null);
    });
  }, []);

  useEffect(() => {
    setSelectedStructure(null);
    setSelectedMeshName("");
  }, [activeChapter?.id, activeModel?.id]);

  function handleChapterSelect(chapter) {
    setActiveChapter(chapter);
    setActiveModel(chapter?.models?.[0] || null);
  }

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
        function: "This mesh or node is not mapped yet. Add it to backend/data/structures.json when you are ready to teach it.",
        attachments: [],
        clinical_notes: [],
        study_prompt: "Map this node to a structure and write a chapter-specific study prompt."
      });
    }
  }

  const chapterStats = activeChapter?.stats || {};

  return (
    <main className="app-shell">
      <aside className="chapter-column">
        <section className="brand-card">
          <p className="eyebrow">BioAtlas Vet Studio</p>
          <h1>Veterinary anatomy in chapters</h1>
          <p>
            Move chapter by chapter, open the model lesson you want, inspect anatomy, and finish each section with a quiz.
          </p>
        </section>

        <ChapterNavigator
          chapters={chapters}
          activeChapter={activeChapter}
          onSelect={handleChapterSelect}
        />
      </aside>

      <section className="main-column">
        <section className="hero chapter-hero">
          <div className="hero-copy">
            <p className="eyebrow">{activeChapter?.eyebrow || "Chapter format"}</p>
            <h2>{activeChapter?.title || "Loading chapters"}</h2>
            <p>{activeChapter?.summary || "Building your study map from the model registry."}</p>
          </div>

          <div className="hero-stats">
            <div className="stat-chip">
              <strong>{chapterStats.model_count || 0}</strong>
              <span>lesson models</span>
            </div>
            <div className="stat-chip">
              <strong>{chapterStats.quiz_count || 0}</strong>
              <span>quiz prompts</span>
            </div>
            <div className="stat-chip">
              <strong>{chapterStats.local_model_count || 0}</strong>
              <span>local GLBs</span>
            </div>
          </div>

          {!!activeChapter?.goals?.length && (
            <div className="chapter-goals">
              {activeChapter.goals.map((goal) => (
                <span key={goal} className="goal-pill">{goal}</span>
              ))}
            </div>
          )}
        </section>

        <ModelRegistry
          models={activeChapter?.models || []}
          activeModel={activeModel}
          onSelect={setActiveModel}
          chapterTitle={activeChapter?.title}
        />

        <AnatomyViewer
          model={activeModel}
          selectedId={selectedStructure?.id}
          onStructureClick={handleStructureClick}
          chapterTitle={activeChapter?.title}
        />
      </section>

      <aside className="side-column">
        <InfoPanel
          structure={selectedStructure}
          meshName={selectedMeshName}
          model={activeModel}
          chapter={activeChapter}
        />
        <QuizEngine
          species={activeModel?.species}
          system={activeModel?.system}
          chapterTitle={activeChapter?.title}
        />
      </aside>
    </main>
  );
}
