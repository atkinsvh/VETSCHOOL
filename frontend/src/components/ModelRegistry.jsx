function statusLabel(model) {
  if (model.mode === "local") return "Local GLB ready";
  if (model.download_status === "downloaded") return "Downloaded";
  if (model.mode === "placeholder") return "Placeholder lesson";
  return "Source-linked lesson";
}


export default function ModelRegistry({ models, activeModel, onSelect, chapterTitle }) {
  return (
    <section className="registry-card">
      <div className="section-heading">
        <p className="eyebrow">Chapter Models</p>
        <h2>{chapterTitle ? `${chapterTitle} lessons` : "Lesson library"}</h2>
        <p>Open a model, inspect a structure, and keep the quiz in the same study flow.</p>
      </div>

      <div className="model-list">
        {models.map((model) => (
          <button
            key={model.id}
            className={activeModel?.id === model.id ? "model-button active" : "model-button"}
            onClick={() => onSelect(model)}
          >
            <strong>{model.title}</strong>
            <span>{model.species} · {model.system}</span>
            <span className="model-status">{statusLabel(model)}</span>
          </button>
        ))}
      </div>

      {activeModel?.source_url && (
        <a className="source-link" href={activeModel.source_url} target="_blank" rel="noreferrer">
          Open current source model page
        </a>
      )}
    </section>
  );
}
