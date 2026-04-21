import { NavLink, Route, Routes, Navigate } from "react-router-dom";
import { useEffect, useState } from "react";
import ChatPage from "./pages/ChatPage.jsx";
import KnowledgeBasePage from "./pages/KnowledgeBasePage.jsx";
import SyntheticPage from "./pages/SyntheticPage.jsx";
import DocsGenPage from "./pages/DocsGenPage.jsx";
import MetricsPage from "./pages/MetricsPage.jsx";
import AgentPage from "./pages/AgentPage.jsx";
import { api } from "./api/client.js";

const nav = [
  { to: "/chat", label: "Chat", icon: "💬" },
  { to: "/agent", label: "Research Agent", icon: "🤖" },
  { to: "/knowledge-base", label: "Knowledge Base", icon: "📚" },
  { to: "/docs-gen", label: "Doc Generator", icon: "📝" },
  { to: "/synthetic", label: "Synthetic Data", icon: "🧪" },
  { to: "/metrics", label: "Metrics", icon: "📈" },
];

export default function App() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth({ status: "down" }));
  }, []);

  return (
    <div className="flex h-full">
      <aside className="w-64 shrink-0 bg-ink-900 border-r border-ink-800 flex flex-col">
        <div className="px-5 py-5 border-b border-ink-800">
          <div className="text-xl font-bold text-brand-400">DocuMind</div>
          <div className="text-xs text-slate-400 mt-0.5">
            RAG + Synthetic Data + Prompt Engineering
          </div>
        </div>

        <nav className="p-3 space-y-1 flex-1">
          {nav.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition ${
                  isActive
                    ? "bg-brand-600/20 text-brand-400"
                    : "text-slate-300 hover:bg-ink-800 hover:text-white"
                }`
              }
            >
              <span>{n.icon}</span>
              <span>{n.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-ink-800 text-xs text-slate-400">
          {health ? (
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span
                  className={`inline-block w-2 h-2 rounded-full ${
                    health.status === "ok" ? "bg-emerald-400" : "bg-red-400"
                  }`}
                />
                <span>API: {health.status}</span>
              </div>
              <div>Model: <span className="font-mono text-slate-300">{health.model}</span></div>
              <div>Chunks: {health.vector_store_size}</div>
              {health.stub_mode && (
                <div className="text-amber-400 mt-1">⚠️ Stub mode (no API key)</div>
              )}
            </div>
          ) : (
            <div>Checking API…</div>
          )}
        </div>
      </aside>

      <main className="flex-1 overflow-hidden">
        <Routes>
          <Route path="/" element={<Navigate to="/chat" replace />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/agent" element={<AgentPage />} />
          <Route path="/knowledge-base" element={<KnowledgeBasePage />} />
          <Route path="/docs-gen" element={<DocsGenPage />} />
          <Route path="/synthetic" element={<SyntheticPage />} />
          <Route path="/metrics" element={<MetricsPage />} />
        </Routes>
      </main>
    </div>
  );
}
