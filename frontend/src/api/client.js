// Thin fetch wrapper. Uses /api prefix (proxied to FastAPI in dev via Vite).

const BASE = "/api";

async function request(path, { method = "GET", body, signal } = {}) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    signal,
  });

  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: text };
  }

  if (!res.ok) {
    const detail = data?.detail || `HTTP ${res.status}`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

export const api = {
  health: () => request("/health"),
  metrics: () => request("/metrics"),
  ingestUrl: (url) => request("/ingest", { method: "POST", body: { url } }),
  ingestText: (title, text, source) =>
    request("/ingest/text", { method: "POST", body: { title, text, source } }),
  listKB: () => request("/knowledge-base"),
  resetKB: () => request("/knowledge-base", { method: "DELETE" }),
  chat: (query, top_k) => request("/chat", { method: "POST", body: { query, top_k } }),
  generateDocs: (topic, code, use_retrieval = true) =>
    request("/generate-docs", { method: "POST", body: { topic, code, use_retrieval } }),
  synthetic: (doc_id, n_pairs = 5) =>
    request("/synthetic-data", { method: "POST", body: { doc_id, n_pairs } }),
  agentResearch: (topic, num_queries = 3, per_query = 3) =>
    request("/agent/research", {
      method: "POST",
      body: { topic, num_queries, per_query },
    }),
};
