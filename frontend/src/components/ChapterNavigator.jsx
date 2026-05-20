export default function ChapterNavigator({ chapters, activeChapter, onSelect }) {
  return (
    <section className="chapter-card">
      <div className="section-heading">
        <p className="eyebrow">Chapter Map</p>
        <h2>Study by chapter</h2>
        <p>Each chapter groups a species and anatomy system into one study track.</p>
      </div>

      <div className="chapter-list">
        {chapters.map((chapter) => {
          const active = activeChapter?.id === chapter.id;
          const stats = chapter.stats || {};

          return (
            <button
              key={chapter.id}
              className={active ? "chapter-button active" : "chapter-button"}
              onClick={() => onSelect(chapter)}
            >
              <span className="chapter-kicker">{chapter.eyebrow}</span>
              <strong>{chapter.title}</strong>
              <span className="chapter-copy">{chapter.summary}</span>

              <span className="chapter-stats">
                <span>{stats.model_count || 0} models</span>
                <span>{stats.quiz_count || 0} quiz prompts</span>
                <span>{stats.local_model_count || 0} local</span>
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
