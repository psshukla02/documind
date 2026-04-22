import { NavLink, Route, Routes, Navigate, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";

import HomePage from "./pages/HomePage.jsx";
import ChatPage from "./pages/ChatPage.jsx";
import KnowledgeBasePage from "./pages/KnowledgeBasePage.jsx";
import SyntheticPage from "./pages/SyntheticPage.jsx";
import DocsGenPage from "./pages/DocsGenPage.jsx";
import MetricsPage from "./pages/MetricsPage.jsx";
import AgentPage from "./pages/AgentPage.jsx";
import { api } from "./api/client.js";

const NAV = [
  { to: "/",              label: "Home",           icon: "✦" },
  { to: "/chat",          label: "Chat",           icon: "✦" },
  { to: "/agent",         label: "Research Agent", icon: "✦" },
  { to: "/knowledge-base",label: "Knowledge Base", icon: "✦" },
  { to: "/docs-gen",      label: "Doc Generator",  icon: "✦" },
  { to: "/synthetic",     label: "Synthetic Data", icon: "✦" },
  { to: "/metrics",       label: "Metrics",        icon: "✦" },
];

function Sidebar({ health }) {
  return (
    <aside className="w-64 shrink-0 h-full flex flex-col p-3">
      <div className="glass rounded-2xl h-full flex flex-col shadow-card overflow-hidden">
        <div className="px-5 pt-6 pb-5 border-b border-ink-100/80">
          <div className="text-lg font-semibold tracking-tight text-ink-900">
            DocuMind
          </div>
          <div className="mt-1 text-[11px] font-medium uppercase tracking-[0.14em] text-ink-500">
            RAG · Agent · Synthetic
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {NAV.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === "/"}
              className={({ isActive }) =>
                [
                  "group flex items-center gap-3 px-3 py-2 rounded-xl",
                  "text-[14px] transition-all",
                  isActive
                    ? "bg-white text-ink-900 shadow-soft border border-ink-100"
                    : "text-ink-500 hover:text-ink-900 hover:bg-white/60",
                ].join(" ")
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    className={[
                      "w-1.5 h-1.5 rounded-full",
                      isActive ? "bg-brand-500" : "bg-ink-200 group-hover:bg-brand-300",
                    ].join(" ")}
                  />
                  <span className="tracking-tight">{n.label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-ink-100/80 text-[11px] text-ink-500">
          {health ? (
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <span
                  className={[
                    "inline-block w-1.5 h-1.5 rounded-full",
                    health.status === "ok" ? "bg-mint-500" : "bg-rose-500",
                  ].join(" ")}
                />
                <span className="text-ink-700">API: {health.status}</span>
              </div>
              <div>Model: <span className="font-mono text-ink-700">{health.model}</span></div>
              <div>Chunks: <span className="text-ink-700">{health.vector_store_size}</span></div>
              {health.stub_mode && (
                <div className="mt-1 text-peach-400">● Stub mode (no API key)</div>
              )}
            </div>
          ) : (
            <div>Checking API…</div>
          )}
        </div>
      </div>
    </aside>
  );
}

export default function App() {
  const [health, setHealth] = useState(null);
  const location = useLocation();

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth({ status: "down" }));
  }, []);

  return (
    <div className="flex h-full">
      <Sidebar health={health} />

      <main className="flex-1 min-w-0 overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
            className="h-full"
          >
            <Routes location={location}>
              <Route path="/" element={<HomePage />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/agent" element={<AgentPage />} />
              <Route path="/knowledge-base" element={<KnowledgeBasePage />} />
              <Route path="/docs-gen" element={<DocsGenPage />} />
              <Route path="/synthetic" element={<SyntheticPage />} />
              <Route path="/metrics" element={<MetricsPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
