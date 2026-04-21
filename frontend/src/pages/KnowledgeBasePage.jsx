import { useEffect, useState } from "react";
import PageHeader from "../components/PageHeader.jsx";
import Button from "../components/Button.jsx";
import Spinner from "../components/Spinner.jsx";
import { Card, CardBody, CardHeader } from "../components/Card.jsx";
import { api } from "../api/client.js";

export default function KnowledgeBasePage() {
  const [docs, setDocs] = useState([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState("url"); // url | text
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

  useEffect(() => {
    reload();
  }, []);

  const ingest = async () => {
    setError(null);
    setStatus(null);
    setIngesting(true);
    try {
      const res =
        mode === "url"
          ? await api.ingestUrl(url.trim())
          : await api.ingestText(title.trim(), rawText, "manual");
      setStatus(`Ingested "${res.title}" — ${res.chunks} chunks in ${res.latency_ms} ms.`);
      setUrl("");
      setTitle("");
      setRawText("");
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

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <PageHeader
        title="Knowledge Base"
        subtitle={`${docs.length} documents · ${totalChunks} chunks indexed`}
        actions={
          <Button variant="danger" onClick={reset} disabled={docs.length === 0}>
            Clear All
          </Button>
        }
      />

      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
        <Card>
          <CardHeader>Ingest a document</CardHeader>
          <CardBody>
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setMode("url")}
                className={`px-3 py-1.5 text-sm rounded-md ${
                  mode === "url"
                    ? "bg-brand-600 text-white"
                    : "bg-ink-800 text-slate-300"
                }`}
              >
                From URL
              </button>
              <button
                onClick={() => setMode("text")}
                className={`px-3 py-1.5 text-sm rounded-md ${
                  mode === "text"
                    ? "bg-brand-600 text-white"
                    : "bg-ink-800 text-slate-300"
                }`}
              >
                From Text
              </button>
            </div>

            {mode === "url" ? (
              <div className="flex gap-2">
                <input
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://docs.example.com/page"
                  className="flex-1 bg-ink-900 border border-ink-800 rounded-md px-3 py-2 text-sm"
                />
                <Button onClick={ingest} disabled={ingesting || !url}>
                  {ingesting ? "Ingesting…" : "Ingest URL"}
                </Button>
              </div>
            ) : (
              <div className="space-y-2">
                <input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Title"
                  className="w-full bg-ink-900 border border-ink-800 rounded-md px-3 py-2 text-sm"
                />
                <textarea
                  value={rawText}
                  onChange={(e) => setRawText(e.target.value)}
                  placeholder="Paste the content to ingest (minimum 20 chars)…"
                  rows={8}
                  className="w-full bg-ink-900 border border-ink-800 rounded-md px-3 py-2 text-sm font-mono"
                />
                <div className="flex justify-end">
                  <Button
                    onClick={ingest}
                    disabled={ingesting || !title || rawText.length < 20}
                  >
                    {ingesting ? "Ingesting…" : "Ingest Text"}
                  </Button>
                </div>
              </div>
            )}

            {status && (
              <div className="mt-3 text-sm text-emerald-400">{status}</div>
            )}
            {error && <div className="mt-3 text-sm text-red-400">{error}</div>}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>Indexed Documents</CardHeader>
          <CardBody>
            {loading ? (
              <Spinner />
            ) : docs.length === 0 ? (
              <div className="text-sm text-slate-400">
                No documents yet. Ingest a URL or paste text above.
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-400 border-b border-ink-800">
                    <th className="py-2 pr-4">Title</th>
                    <th className="py-2 pr-4">Source</th>
                    <th className="py-2 pr-4 text-right">Chunks</th>
                  </tr>
                </thead>
                <tbody>
                  {docs.map((d) => (
                    <tr key={d.doc_id} className="border-b border-ink-800/60">
                      <td className="py-2 pr-4 text-slate-200">{d.title}</td>
                      <td className="py-2 pr-4 text-slate-400">
                        {d.source.startsWith("http") ? (
                          <a
                            href={d.source}
                            target="_blank"
                            rel="noreferrer"
                            className="text-brand-400 hover:underline truncate block max-w-xs"
                          >
                            {d.source}
                          </a>
                        ) : (
                          d.source
                        )}
                      </td>
                      <td className="py-2 pr-4 text-right text-slate-300">
                        {d.chunks}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
