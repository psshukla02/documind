import { useEffect, useState } from "react";
import { motion } from "framer-motion";

import PageHeader from "../components/PageHeader.jsx";
import PageTransition from "../components/PageTransition.jsx";
import Button from "../components/Button.jsx";
import Spinner from "../components/Spinner.jsx";
import { Card, CardBody, CardHeader, SectionLabel } from "../components/Card.jsx";
import { Input, Textarea } from "../components/Input.jsx";
import { api } from "../api/client.js";

export default function KnowledgeBasePage() {
  const [docs, setDocs] = useState([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState("url");
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const [rawText, setRawText] = useState("");
  const [error, setError] = useState(null);
  const [status, setStatus] = useState(null);
  const [ingesting, setIngesting] = useState(false);

  const reload = async () => {
    setLoading(true);
    try {
      const res = await api.listKB();
      setDocs(res.documents);
      setTotalChunks(res.total_chunks);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { reload(); }, []);

  const ingest = async () => {
    setError(null); setStatus(null); setIngesting(true);
    try {
      const res = mode === "url"
        ? await api.ingestUrl(url.trim())
        : await api.ingestText(title.trim(), rawText, "manual");
      setStatus(`Ingested "${res.title}" — ${res.chunks} chunks in ${res.latency_ms} ms.`);
      setUrl(""); setTitle(""); setRawText("");
      await reload();
    } catch (e) {
      setError(e.message);
    } finally {
      setIngesting(false);
    }
  };

  const reset = async () => {
    if (!confirm("Delete ALL ingested documents? This cannot be undone.")) return;
    try {
      await api.resetKB();
      await reload();
      setStatus("Knowledge base cleared.");
    } catch (e) {
      setError(e.message);
    }
  };

  const Tab = ({ value, children }) => (
    <button
      onClick={() => setMode(value)}
      className={[
        "px-3.5 py-1.5 text-sm rounded-full transition",
        mode === value
          ? "bg-white border border-ink-100 text-ink-900 shadow-soft"
          : "bg-transparent text-ink-500 hover:text-ink-900",
      ].join(" ")}
    >
      {children}
    </button>
  );

  return (
    <PageTransition>
      <div className="h-full flex flex-col overflow-hidden">
        <PageHeader
          kicker={`${docs.length} docs · ${totalChunks} chunks`}
          title="Knowledge Base"
          subtitle="Ingest URLs or paste raw text. The chunker packs paragraphs into overlapping semantic windows before embedding."
          actions={
            <Button variant="ghost" onClick={reset} disabled={docs.length === 0}>
              Clear All
            </Button>
          }
        />

        <div className="flex-1 overflow-y-auto px-10 pb-10 space-y-6">
          <Card>
            <CardHeader>Ingest a document</CardHeader>
            <CardBody>
              <div className="inline-flex gap-1 p-1 bg-ink-50 rounded-full mb-5">
                <Tab value="url">From URL</Tab>
                <Tab value="text">From Text</Tab>
              </div>

              {mode === "url" ? (
                <div className="flex gap-2">
                  <Input
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://docs.example.com/page"
                  />
                  <Button onClick={ingest} disabled={ingesting || !url}>
                    {ingesting ? "Ingesting…" : "Ingest"}
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  <Input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Title"
                  />
                  <Textarea
                    value={rawText}
                    onChange={(e) => setRawText(e.target.value)}
                    placeholder="Paste the content to ingest (minimum 20 chars)…"
                    rows={8}
                  />
                  <div className="flex justify-end">
                    <Button onClick={ingest} disabled={ingesting || !title || rawText.length < 20}>
                      {ingesting ? "Ingesting…" : "Ingest Text"}
                    </Button>
                  </div>
                </div>
              )}

              {status && <div className="mt-4 text-sm text-mint-500">{status}</div>}
              {error  && <div className="mt-4 text-sm text-rose-500">{error}</div>}
            </CardBody>
          </Card>

          <Card>
            <CardHeader>Indexed Documents</CardHeader>
            <CardBody>
              {loading ? (
                <Spinner label="Loading…" />
              ) : docs.length === 0 ? (
                <div className="text-center py-10">
                  <div className="text-4xl mb-2 opacity-30">📚</div>
                  <div className="text-sm text-ink-500">
                    No documents yet. Ingest a URL, paste text above, or use the Research Agent.
                  </div>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left">
                        <th className="py-2 pr-4 text-[11px] uppercase tracking-[0.14em] text-ink-500 font-semibold">Title</th>
                        <th className="py-2 pr-4 text-[11px] uppercase tracking-[0.14em] text-ink-500 font-semibold">Source</th>
                        <th className="py-2 pr-4 text-[11px] uppercase tracking-[0.14em] text-ink-500 font-semibold text-right">Chunks</th>
                      </tr>
                    </thead>
                    <tbody>
                      {docs.map((d, i) => (
                        <motion.tr
                          key={d.doc_id}
                          initial={{ opacity: 0, y: 4 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: i * 0.02 }}
                          className="border-t border-ink-100 hover:bg-ink-50/60 transition"
                        >
                          <td className="py-3 pr-4 text-ink-900 font-medium">{d.title}</td>
                          <td className="py-3 pr-4 text-ink-500">
                            {d.source.startsWith("http") ? (
                              <a href={d.source} target="_blank" rel="noreferrer"
                                 className="text-brand-600 hover:underline truncate block max-w-xs">
                                {d.source}
                              </a>
                            ) : d.source}
                          </td>
                          <td className="py-3 pr-4 text-right text-ink-700 font-mono">{d.chunks}</td>
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardBody>
          </Card>
        </div>
      </div>
    </PageTransition>
  );
}
