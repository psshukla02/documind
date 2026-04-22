import { useState } from "react";
import PageHeader from "../components/PageHeader.jsx";
import PageTransition from "../components/PageTransition.jsx";
import Button from "../components/Button.jsx";
import Spinner from "../components/Spinner.jsx";
import CopyButton from "../components/CopyButton.jsx";
import Markdown from "../components/Markdown.jsx";
import { Card, CardBody, CardHeader } from "../components/Card.jsx";
import { Input, Textarea } from "../components/Input.jsx";
import { api } from "../api/client.js";

export default function DocsGenPage() {
  const [topic, setTopic] = useState("");
  const [code, setCode] = useState("");
  const [useRetrieval, setUseRetrieval] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const run = async () => {
    setError(null); setResult(null);
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
    <PageTransition>
      <div className="h-full flex flex-col overflow-hidden">
        <PageHeader
          kicker="Markdown · Publication-quality"
          title="Documentation Generator"
          subtitle="Describe a topic or paste code — get structured Markdown docs, optionally grounded in your knowledge base."
        />

        <div className="flex-1 overflow-y-auto px-10 pb-10 space-y-6">
          <Card>
            <CardHeader>Input</CardHeader>
            <CardBody>
              <div className="space-y-3">
                <Input
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder='Topic (e.g. "How to use FastAPI dependency injection")'
                />
                <Textarea
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="Optional code snippet to document…"
                  rows={8}
                />
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 text-sm text-ink-700 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={useRetrieval}
                      onChange={(e) => setUseRetrieval(e.target.checked)}
                      className="accent-brand-500"
                    />
                    Ground in knowledge base (RAG)
                  </label>
                  <Button onClick={run} disabled={loading}>
                    {loading ? "Generating…" : "Generate Docs"}
                  </Button>
                </div>
              </div>
              {error && <div className="mt-3 text-sm text-rose-500">{error}</div>}
            </CardBody>
          </Card>

          {loading && <Spinner label="Composing documentation…" />}

          {result && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <span>Generated Documentation</span>
                  <div className="flex items-center gap-3 text-xs text-ink-500 font-normal">
                    <span>{result.latency_ms?.toFixed?.(0)} ms</span>
                    <span className="font-mono">{result.model}</span>
                    <CopyButton text={result.markdown} label="Copy Markdown" />
                  </div>
                </div>
              </CardHeader>
              <CardBody>
                <Markdown>{result.markdown}</Markdown>

                {result.citations?.length > 0 && (
                  <div className="mt-5 pt-4 border-t border-ink-100">
                    <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-ink-500 mb-2">
                      Reference Sources
                    </div>
                    <ul className="space-y-1.5 text-sm">
                      {result.citations.map((c) => (
                        <li key={c.id} className="flex gap-2 items-center">
                          <span className="cite-chip">{c.id}</span>
                          <a href={c.url} target="_blank" rel="noreferrer" className="text-brand-600 hover:underline">
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
    </PageTransition>
  );
}
