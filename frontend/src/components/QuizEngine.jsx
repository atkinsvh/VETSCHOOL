import { useEffect, useState } from "react";
import { api } from "../lib/api.js";

export default function QuizEngine({ species, system, chapterTitle }) {
  const [questions, setQuestions] = useState([]);
  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState("");
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (!species || !system) return;
    setIndex(0);
    setSelected("");
    setChecked(false);
    api.quizzes(species, system).then(setQuestions).catch(() => setQuestions([]));
  }, [species, system]);

  const question = questions[index];

  if (!question) {
    return (
      <section className="panel">
        <p className="eyebrow">Chapter Quiz</p>
        <h2>{chapterTitle || "No chapter selected"}</h2>
        <p>
          {species && system
            ? "This chapter does not have quiz prompts yet. You can still explore the model and map structures."
            : "Choose a chapter to load its quiz prompts."}
        </p>
      </section>
    );
  }

  const correct = selected === question.answer;

  return (
    <section className="panel">
      <p className="eyebrow">Chapter Quiz · {index + 1}/{questions.length}</p>
      <h2>{question.question}</h2>
      {chapterTitle && <p className="small">From {chapterTitle}</p>}

      <div className="choices">
        {question.choices.map((choice) => (
          <button
            key={choice}
            className={selected === choice ? "choice selected" : "choice"}
            onClick={() => { setSelected(choice); setChecked(false); }}
          >
            {choice}
          </button>
        ))}
      </div>

      <div className="quiz-actions">
        <button disabled={!selected} onClick={() => setChecked(true)}>Check</button>
        <button onClick={() => {
          setIndex((index + 1) % questions.length);
          setSelected("");
          setChecked(false);
        }}>Next</button>
      </div>

      {checked && (
        <div className={correct ? "feedback correct" : "feedback incorrect"}>
          <strong>{correct ? "Correct." : "Not quite."}</strong>
          <p>{question.explanation}</p>
        </div>
      )}
    </section>
  );
}
