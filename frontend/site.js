(function () {
  const bundle = window.BIOATLAS_DATA || {};
  const chapters = bundle.chapters || [];
  const quizzes = bundle.quizzes || {};
  const structures = bundle.structures || {};

  const state = {
    chapters,
    activeChapter: chapters[0] || null,
    activeModel: chapters[0]?.models?.[0] || null,
    activeStructureId: null,
    quizIndex: 0,
    quizSelected: "",
    quizChecked: false
  };

  const elements = {
    chapterList: document.getElementById("chapter-list"),
    chapterEyebrow: document.getElementById("chapter-eyebrow"),
    chapterTitle: document.getElementById("chapter-title"),
    chapterSummary: document.getElementById("chapter-summary"),
    chapterStats: document.getElementById("chapter-stats"),
    chapterGoals: document.getElementById("chapter-goals"),
    lessonTitle: document.getElementById("lesson-title"),
    modelList: document.getElementById("model-list"),
    viewerName: document.getElementById("viewer-name"),
    viewerStatus: document.getElementById("viewer-status"),
    viewerSurface: document.getElementById("viewer-surface"),
    viewerNote: document.getElementById("viewer-note"),
    notesTitle: document.getElementById("notes-title"),
    notesCopy: document.getElementById("notes-copy"),
    lessonTags: document.getElementById("lesson-tags"),
    structureList: document.getElementById("structure-list"),
    structurePanel: document.getElementById("structure-panel"),
    sourceLink: document.getElementById("source-link"),
    quizTitle: document.getElementById("quiz-title"),
    quizEmpty: document.getElementById("quiz-empty"),
    quizCard: document.getElementById("quiz-card"),
    quizProgress: document.getElementById("quiz-progress"),
    quizQuestion: document.getElementById("quiz-question"),
    quizChoices: document.getElementById("quiz-choices"),
    quizCheck: document.getElementById("quiz-check"),
    quizNext: document.getElementById("quiz-next"),
    quizFeedback: document.getElementById("quiz-feedback")
  };

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function titleForModel(model) {
    return model?.model_name || model?.title || model?.id || "Untitled model";
  }

  function systemForModel(model) {
    return model?.anatomy_system || model?.system || "unknown";
  }

  function localPathToRelative(localPath) {
    if (!localPath) return "";
    return `../public${localPath}`;
  }

  function isDirectGlb(url) {
    return Boolean(url) && url.toLowerCase().split("?", 1)[0].endsWith(".glb");
  }

  function deriveEmbedUrl(model) {
    if (model?.embed_url) return model.embed_url;
    const source = model?.source_url || "";
    const match = source.match(/https:\/\/sketchfab\.com\/3d-models\/[^/]+-([a-f0-9]{32})/i);
    if (match) return `https://sketchfab.com/models/${match[1]}/embed`;
    return "";
  }

  function modelStatus(model) {
    if (!model) return "No lesson selected";
    if (model.mode === "local") return "Local GLB ready";
    if (model.download_status === "downloaded") return "Downloaded";
    if (model.mode === "placeholder") return "Placeholder study mode";
    return "Source-linked lesson";
  }

  function availableStructures(model) {
    if (!model) return [];
    const species = model.species;
    const system = systemForModel(model);
    const structureMap = structures?.[species]?.[system] || {};
    const preferred = Array.from(new Set(model.clickable_nodes || []))
      .filter((id) => structureMap[id])
      .map((id) => structureMap[id]);
    const fallback = Object.values(structureMap).filter((item) => !preferred.some((entry) => entry.id === item.id));
    return preferred.concat(fallback).slice(0, 12);
  }

  function activeStructure() {
    const model = state.activeModel;
    if (!model || !state.activeStructureId) return null;
    const species = model.species;
    const system = systemForModel(model);
    return structures?.[species]?.[system]?.[state.activeStructureId] || null;
  }

  function chapterQuizItems() {
    const chapter = state.activeChapter;
    if (!chapter) return [];
    return quizzes?.[chapter.species]?.[chapter.system] || [];
  }

  function ensureActiveStructure() {
    const options = availableStructures(state.activeModel);
    if (!options.length) {
      state.activeStructureId = null;
      return;
    }
    if (!state.activeStructureId || !options.some((item) => item.id === state.activeStructureId)) {
      state.activeStructureId = options[0].id;
    }
  }

  function setChapter(chapterId) {
    const chapter = state.chapters.find((item) => item.id === chapterId) || state.chapters[0] || null;
    state.activeChapter = chapter;
    state.activeModel = chapter?.models?.[0] || null;
    state.quizIndex = 0;
    state.quizSelected = "";
    state.quizChecked = false;
    state.activeStructureId = null;
    ensureActiveStructure();
    render();
  }

  function setModel(modelId) {
    const model = (state.activeChapter?.models || []).find((item) => item.id === modelId) || state.activeChapter?.models?.[0] || null;
    state.activeModel = model;
    state.activeStructureId = null;
    ensureActiveStructure();
    render();
  }

  function setStructure(structureId) {
    state.activeStructureId = structureId;
    renderNotes();
  }

  function renderChapters() {
    if (!state.chapters.length) {
      elements.chapterList.innerHTML = "<p>No chapters found in the bundled data.</p>";
      return;
    }

    elements.chapterList.innerHTML = state.chapters.map((chapter) => {
      const active = state.activeChapter?.id === chapter.id ? " active" : "";
      const stats = chapter.stats || {};
      return `
        <button class="chapter-button${active}" type="button" data-chapter-id="${escapeHtml(chapter.id)}">
          <span class="chapter-kicker">${escapeHtml(chapter.eyebrow)}</span>
          <strong>${escapeHtml(chapter.title)}</strong>
          <span class="chapter-copy">${escapeHtml(chapter.summary)}</span>
          <span class="chapter-stats">
            <span>${stats.model_count || 0} models</span>
            <span>${stats.quiz_count || 0} quiz prompts</span>
            <span>${stats.local_model_count || 0} local</span>
          </span>
        </button>
      `;
    }).join("");

    elements.chapterList.querySelectorAll("[data-chapter-id]").forEach((button) => {
      button.addEventListener("click", () => setChapter(button.dataset.chapterId));
    });
  }

  function renderChapterHero() {
    const chapter = state.activeChapter;
    if (!chapter) {
      elements.chapterEyebrow.textContent = "Chapter format";
      elements.chapterTitle.textContent = "No chapters available";
      elements.chapterSummary.textContent = "The bundled site data did not include any chapter records.";
      elements.chapterStats.innerHTML = "";
      elements.chapterGoals.innerHTML = "";
      return;
    }

    elements.chapterEyebrow.textContent = chapter.eyebrow;
    elements.chapterTitle.textContent = chapter.title;
    elements.chapterSummary.textContent = chapter.summary;
    elements.lessonTitle.textContent = `${chapter.title} lessons`;

    elements.chapterStats.innerHTML = `
      <div class="stat-chip"><strong>${chapter.stats.model_count || 0}</strong><span>lesson models</span></div>
      <div class="stat-chip"><strong>${chapter.stats.quiz_count || 0}</strong><span>quiz prompts</span></div>
      <div class="stat-chip"><strong>${chapter.stats.local_model_count || 0}</strong><span>local GLBs</span></div>
    `;

    elements.chapterGoals.innerHTML = (chapter.goals || [])
      .map((goal) => `<span class="goal-pill">${escapeHtml(goal)}</span>`)
      .join("");
  }

  function renderModels() {
    const models = state.activeChapter?.models || [];
    if (!models.length) {
      elements.modelList.innerHTML = "<p>No models are registered for this chapter.</p>";
      return;
    }

    elements.modelList.innerHTML = models.map((model) => {
      const active = state.activeModel?.id === model.id ? " active" : "";
      return `
        <button class="model-button${active}" type="button" data-model-id="${escapeHtml(model.id)}">
          <strong>${escapeHtml(titleForModel(model))}</strong>
          <span>${escapeHtml(model.species)} · ${escapeHtml(systemForModel(model))}</span>
          <span class="model-status">${escapeHtml(modelStatus(model))}</span>
        </button>
      `;
    }).join("");

    elements.modelList.querySelectorAll("[data-model-id]").forEach((button) => {
      button.addEventListener("click", () => setModel(button.dataset.modelId));
    });
  }

  function renderViewer() {
    const model = state.activeModel;
    if (!model) {
      elements.viewerName.textContent = "No lesson selected";
      elements.viewerStatus.textContent = "Choose a chapter to begin.";
      elements.viewerSurface.innerHTML = `
        <div class="viewer-copy">
          <h3>Chapter portal ready</h3>
          <p>Select a chapter from the left to load its lessons, structures, and quiz prompts.</p>
        </div>
      `;
      elements.viewerNote.textContent = "The portal will use a local GLB when one is available, otherwise it will show a source-based preview or study note.";
      return;
    }

    const title = titleForModel(model);
    const localFile = localPathToRelative(model.local_glb_path || model.local_file);
    const embedUrl = deriveEmbedUrl(model);
    const directGlb = isDirectGlb(model.source_url) ? model.source_url : "";
    const viewerStatus = model.mode === "local" || model.download_status === "downloaded"
      ? `Viewing local lesson at ${model.local_glb_path || model.local_file}`
      : embedUrl
        ? "Showing Sketchfab lesson preview"
        : directGlb
          ? "Showing direct GLB lesson preview"
          : "Showing study guidance for this lesson";

    elements.viewerName.textContent = title;
    elements.viewerStatus.textContent = viewerStatus;

    if (model.mode === "local" || model.download_status === "downloaded") {
      elements.viewerSurface.innerHTML = `
        <model-viewer
          class="viewer-model"
          src="${escapeHtml(localFile)}"
          camera-controls
          touch-action="pan-y"
          autoplay
          shadow-intensity="1"
          exposure="1.1"
          alt="${escapeHtml(title)}"
        ></model-viewer>
      `;
      elements.viewerNote.textContent = `Expected local file: public${model.local_glb_path || model.local_file}`;
      return;
    }

    if (embedUrl) {
      elements.viewerSurface.innerHTML = `
        <iframe
          class="viewer-frame"
          src="${escapeHtml(embedUrl)}"
          title="${escapeHtml(title)}"
          allow="autoplay; fullscreen; xr-spatial-tracking"
          allowfullscreen
        ></iframe>
      `;
      elements.viewerNote.textContent = "This lesson is shown through the source platform because a local GLB is not bundled yet.";
      return;
    }

    if (directGlb) {
      elements.viewerSurface.innerHTML = `
        <model-viewer
          class="viewer-model"
          src="${escapeHtml(directGlb)}"
          camera-controls
          touch-action="pan-y"
          shadow-intensity="1"
          alt="${escapeHtml(title)}"
        ></model-viewer>
      `;
      elements.viewerNote.textContent = "This lesson is using a direct GLB source URL.";
      return;
    }

    elements.viewerSurface.innerHTML = `
      <div class="viewer-copy">
        <h3>${escapeHtml(title)}</h3>
        <p>${escapeHtml(model.license_usage_notes || model.notes || "This lesson currently points to an external source rather than a local GLB.")}</p>
        <p>When you obtain the model file, place it at <code>public${escapeHtml(model.local_glb_path || model.local_file || "/models/...")}</code> so the site can render it directly.</p>
      </div>
    `;
    elements.viewerNote.textContent = "No embeddable preview is available for this lesson yet.";
  }

  function renderNotes() {
    const chapter = state.activeChapter;
    const model = state.activeModel;
    const structure = activeStructure();
    const structureOptions = availableStructures(model);

    elements.notesTitle.textContent = model ? titleForModel(model) : "Choose a lesson";
    elements.notesCopy.textContent = model
      ? (model.license_usage_notes || model.notes || `Study ${titleForModel(model)} in the context of ${chapter?.title || "this chapter"}.`)
      : "Select a chapter and lesson to load anatomy notes.";

    elements.lessonTags.innerHTML = (model?.tags || [])
      .slice(0, 8)
      .map((tag) => `<span class="tag-chip">${escapeHtml(tag)}</span>`)
      .join("");

    elements.structureList.innerHTML = structureOptions.map((item) => {
      const active = item.id === state.activeStructureId ? " active" : "";
      return `<button class="structure-chip${active}" type="button" data-structure-id="${escapeHtml(item.id)}">${escapeHtml(item.name)}</button>`;
    }).join("");

    elements.structureList.querySelectorAll("[data-structure-id]").forEach((button) => {
      button.addEventListener("click", () => setStructure(button.dataset.structureId));
    });

    if (structure) {
      elements.structurePanel.classList.remove("hidden");
      elements.structurePanel.innerHTML = `
        <strong>${escapeHtml(structure.name)}</strong>
        <p>${escapeHtml(structure.function || "")}</p>
        <p><strong>Region:</strong> ${escapeHtml(structure.region || "Unmapped")}</p>
        <p><strong>Attachments:</strong> ${escapeHtml((structure.attachments || []).join(", ") || "None listed")}</p>
        <p><strong>Clinical notes:</strong> ${escapeHtml((structure.clinical_notes || []).join(", ") || "None listed")}</p>
        <p><strong>Study prompt:</strong> ${escapeHtml(structure.study_prompt || "Write a short revision prompt for this structure.")}</p>
      `;
    } else if (model) {
      elements.structurePanel.classList.remove("hidden");
      elements.structurePanel.innerHTML = `
        <strong>Structure notes</strong>
        <p>No mapped structures were found for this lesson yet. You can still use the chapter quiz and the model source while building out notes.</p>
      `;
    } else {
      elements.structurePanel.classList.add("hidden");
      elements.structurePanel.innerHTML = "";
    }

    if (model?.source_url) {
      elements.sourceLink.href = model.source_url;
      elements.sourceLink.classList.remove("hidden");
      elements.sourceLink.textContent = "Open source page";
    } else {
      elements.sourceLink.classList.add("hidden");
      elements.sourceLink.removeAttribute("href");
    }
  }

  function renderQuiz() {
    const chapter = state.activeChapter;
    const items = chapterQuizItems();

    elements.quizTitle.textContent = chapter ? chapter.title : "No chapter selected";

    if (!items.length) {
      elements.quizCard.classList.add("hidden");
      elements.quizEmpty.classList.remove("hidden");
      elements.quizEmpty.textContent = chapter
        ? "This chapter does not have quiz prompts yet. You can still study the lesson notes and model sources."
        : "Choose a chapter to load quiz prompts.";
      return;
    }

    const question = items[state.quizIndex % items.length];
    const correct = state.quizSelected === question.answer;

    elements.quizCard.classList.remove("hidden");
    elements.quizEmpty.classList.add("hidden");
    elements.quizProgress.textContent = `Question ${state.quizIndex + 1} of ${items.length}`;
    elements.quizQuestion.textContent = question.question;

    elements.quizChoices.innerHTML = question.choices.map((choice) => {
      const selected = state.quizSelected === choice ? " selected" : "";
      return `<button class="choice${selected}" type="button" data-choice="${escapeHtml(choice)}">${escapeHtml(choice)}</button>`;
    }).join("");

    elements.quizChoices.querySelectorAll("[data-choice]").forEach((button) => {
      button.addEventListener("click", () => {
        state.quizSelected = button.dataset.choice;
        state.quizChecked = false;
        renderQuiz();
      });
    });

    elements.quizCheck.disabled = !state.quizSelected;
    elements.quizCheck.onclick = function () {
      state.quizChecked = true;
      renderQuiz();
    };

    elements.quizNext.onclick = function () {
      state.quizIndex = (state.quizIndex + 1) % items.length;
      state.quizSelected = "";
      state.quizChecked = false;
      renderQuiz();
    };

    if (state.quizChecked) {
      elements.quizFeedback.className = `feedback ${correct ? "correct" : "incorrect"}`;
      elements.quizFeedback.classList.remove("hidden");
      elements.quizFeedback.innerHTML = `
        <strong>${correct ? "Correct." : "Not quite."}</strong>
        <p>${escapeHtml(question.explanation || "")}</p>
      `;
    } else {
      elements.quizFeedback.className = "feedback hidden";
      elements.quizFeedback.innerHTML = "";
    }
  }

  function render() {
    renderChapters();
    renderChapterHero();
    renderModels();
    ensureActiveStructure();
    renderViewer();
    renderNotes();
    renderQuiz();
  }

  render();
})();
