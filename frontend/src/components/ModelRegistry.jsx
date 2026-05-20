export default function ModelRegistry({ models, activeModel, onSelect }) {
  return (
    <section className="registry-card">
      <div>
        <p className="eyebrow">Model Registry</p>
        <h2>Registered Sources</h2>
      </div>

      <div className="model-list">
        {models.map((model) => (
          <button
            key={model.id}
            className={activeModel?.id === model.id ? "model-button active" : "model-button"}
            onClick={() => onSelect(model)}
          >
            <strong>{model.title}</strong>
            <span>{model.species} · {model.system} · {model.mode}</span>
          </button>
        ))}
      </div>

      {activeModel?.source_url && (
        <a className="source-link" href={activeModel.source_url} target="_blank" rel="noreferrer">
          Open source model page
        </a>
      )}
    </section>
  );
}
