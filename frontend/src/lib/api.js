const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

async function request(path) {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) throw new Error(`API error ${response.status}`);
  return response.json();
}

export const api = {
  chapters: () => request("/api/chapters"),
  species: () => request("/api/species"),
  models: () => request("/api/models"),
  model: (species, system) => request(`/api/models/${species}/${system}`),
  structure: (species, system, id) => request(`/api/structures/${species}/${system}/${id}`),
  quizzes: (species, system) => request(`/api/quizzes/${species}/${system}`)
};
