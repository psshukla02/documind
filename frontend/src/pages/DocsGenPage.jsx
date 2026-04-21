import { useState } from "react";
import PageHeader from "../components/PageHeader.jsx";
import Button from "../components/Button.jsx";
import Spinner from "../components/Spinner.jsx";
import CopyButton from "../components/CopyButton.jsx";
import Markdown from "../components/Markdown.jsx";
import { Card, CardBody, CardHeader } from "../components/Card.jsx";
import { api } from "../api/client.js";

export default function DocsGenPage() {
  const [topic, setTopic] = useState("");
  const [code, setCode] = useState("");
  const [useRetrieval, setUseRetrieval] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const run = async () => {
    setError(null);
    setResult(null);
    if (!topic.trim()) {
      setError("Topic is required.");
      return;
    }
    setLoading(true);
    try {
      const res = await api.generateDocs(topic, code || null, useRetrieval);
      setResult(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <PageHeader
        title="Documentation Generator"
        subtitle="Describe a topic or paste code — get publication-quality Markdown docs"
      />
      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
        <Card>
          <CardHeader>Input</CardHeader>
          <CardBody>
            <div className="space-y-3">
              <input
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder='Topic (e.g. "How to use FastAPI dependency injection")'
                className="w-full bg-ink-900 border border-ink-800 rounded-md px-3 py-2 text-sm"
              />
              <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="Optional code snippet to document…"
                rows={8}
                className="w-full bg-ink-900 border border-ink-800 rounded-md px-3 py-2 text-sm font-mono"
              />
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm text-slate-300">
                  <input
                    type="checkbox"
                    checked={useRetrieval}
                    onChange={(e) => setUseRetrieval(e.target.checked)}
                  />
                  Ground in knowledge base (RAG)
                </label>
                <Button onClick={run} disabled={loading}>
                  {loading ? "Generating…" : "Generate Docs"}
                </Button>
              </div>
            </div>
            {error && <div className="mt-3 text-sm text-red-400">{error}</div>}
          </CardBody>
        </Card>

        {loading && <Spinner label="Composing documentation…" />}

        {result && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <span>Generated Documentation</span>
                <div className="flex items-center gap-3 text-xs text-slate-400 font-normal">
                  <span>{result.latency_ms?.toFixed?.(0)} ms</span>
                  <span>{result.model}</span>
                  <CopyButton text={result.markdown} label="Copy Markdown" />
                </div>
              </div>
            </CardHeader>
            <CardBody>
              <Markdown>{result.markdown}</Markdown>

              {result.citations?.length > 0 && (
                <div className="mt-4 pt-3 border-t border-ink-800">
                  <div className="text-xs uppercase tracking-wider text-slate-400 mb-2">
                    Reference Sources
                  </div>
                  <ul className="space-y-1 text-sm">
                    {result.citations.map((c) => (
                      <li key={c.id} className="flex gap-2">
                        <span className="cite-chip">{c.id}</span>
                        <a
                          href={c.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-brand-400 hover:underline"
                        >
                          {c.title}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardBody>
          </Card>
        )}
      </div>
    </div>
  );
}
