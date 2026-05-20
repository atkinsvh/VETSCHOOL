export default function InfoPanel({ structure, meshName, model, chapter }) {
  if (!structure) {
    return (
      <section className="panel">
        <p className="eyebrow">Study Notes</p>
        <h2>{model?.title || "Choose a lesson"}</h2>
        <p>
          {model
            ? "Select a node or mesh in the viewer to load anatomy notes. Until then, use this panel as your chapter briefing."
            : "Pick a chapter and lesson to begin studying."}
        </p>

        {chapter && (
          <div className="chapter-brief">
            <strong>{chapter.title}</strong>
            <p>{chapter.summary}</p>
          </div>
        )}

        {model && (
          <>
            <div className="meta-stack">
              <p className="small">Mode: {model.mode}</p>
              <p className="small">Status: {model.download_status}</p>
              {model.notes && <p className="small">{model.notes}</p>}
            </div>

            {!!model.tags?.length && (
              <div className="tag-row">
                {model.tags.map((tag) => (
                  <span key={tag} className="tag-chip">{tag}</span>
                ))}
              </div>
            )}

            {model.source_url && (
              <a className="source-link" href={model.source_url} target="_blank" rel="noreferrer">
                Review the source page for this lesson
              </a>
            )}
          </>
        )}
      </section>
    );
  }

  return (
    <section className="panel">
      <p className="eyebrow">{structure.system} · {structure.region}</p>
      <h2>{structure.name}</h2>
      {meshName && <p className="mesh-name">Mesh/node: <code>{meshName}</code></p>}
      <p>{structure.function}</p>

      <h3>Attachments</h3>
      <ul>{(structure.attachments || []).map((item) => <li key={item}>{item}</li>)}</ul>

      <h3>Clinical notes</h3>
      <ul>{(structure.clinical_notes || []).map((item) => <li key={item}>{item}</li>)}</ul>

      {structure.study_prompt && (
        <div className="study-prompt">
          <strong>Chapter reflection</strong>
          <p>{structure.study_prompt}</p>
        </div>
      )}
    </section>
  );
}
