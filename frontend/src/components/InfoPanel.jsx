export default function InfoPanel({ structure, meshName, model }) {
  if (!structure) {
    return (
      <section className="panel">
        <p className="eyebrow">Structure Inspector</p>
        <h2>Click a node or mesh</h2>
        <p>The app will inspect the selected mesh name and ask the API for matching anatomy metadata.</p>
        {model?.source_url && (
          <p className="small">Current source: {model.source}</p>
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
          <strong>Extended response</strong>
          <p>{structure.study_prompt}</p>
        </div>
      )}
    </section>
  );
}
