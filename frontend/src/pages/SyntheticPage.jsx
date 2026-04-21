import { useEffect, useState } from "react";
import PageHeader from "../components/PageHeader.jsx";
import Button from "../components/Button.jsx";
import Spinner from "../components/Spinner.jsx";
import CopyButton from "../components/CopyButton.jsx";
import { Card, CardBody, CardHeader } from "../components/Card.jsx";
import { api } from "../api/client.js";

const CAT_COLORS = {
  factual: "bg-sky-600/30 text-sky-300 border-sky-600/40",
  reasoning: "bg-emerald-600/30 text-emerald-300 border-emerald-600/40",
  edge_case: "bg-amber-600/30 text-amber-300 border-amber-600/40",
  example: "bg-fuchsia-600/30 text-fuchsia-300 border-fuchsia-600/40",
};

export default function SyntheticPage() {
  const [docs, setDocs] = useState([]);
  const [docId, setDocId] = useState("");
  const [nPairs, setNPairs] = useState(5);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.listKB().then((r) => setDocs(r.documents)).catch(() => {});
  }, []);

  const run = async () => {
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const res = await api.synthetic(docId || null, nPairs);
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
        title="Synthetic Data Generator"
        subtitle="Generate diverse Q&A pairs from an ingested document"
      />
      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
        <Card>
          <CardHeader>Configuration</CardHeader>
          <CardBody>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs text-slate-400 mb-1">
                  Source Document
                </label>
                <select
                  value={docId}
                  onChange={(e) => setDocId(e.target.value)}
                  className="w-full bg-ink-900 border border-ink-800 rounded-md px-3 py-2 text-sm"
                >
                  <option value="">(any — use first doc)</option>
                  {docs.map((d) => (
                    <option key={d.doc_id} value={d.doc_id}>
                      {d.title} ({d.chunks} chunks)
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">
                  Number of Pairs
                </label>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={nPairs}
                  onChange={(e) => setNPairs(Number(e.target.value))}
                  className="w-full bg-ink-900 border border-ink-800 rounded-md px-3 py-2 text-sm"
                />
              </div>
              <div className="flex items-end">
                <Button onClick={run} disabled={loading || docs.length === 0}>
                  {loading ? "Generating…" : "Generate"}
                </Button>
              </div>
            </div>
            {docs.length === 0 && (
              <div className="mt-3 text-sm text-amber-400">
                Knowledge base is empty — ingest a document first.
              </div>
            )}
            {error && <div className="mt-3 text-sm text-red-400">{error}</div>}
          </CardBody>
        </Card>

        {loading && <Spinner label="Generating synthetic Q&A pairs…" />}

        {result && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <span>
                  {result.pairs.length} pairs · {result.title}
                </span>
                <div className="flex items-center gap-3 text-xs text-slate-400 font-normal">
                  <span>{result.latency_ms?.toFixed?.(0)} ms</span>
                  <CopyButton
                    text={JSON.stringify(result.pairs, null, 2)}
                    label="Copy JSON"
                  />
                </div>
              </div>
            </CardHeader>
            <CardBody>
              {result.pairs.length === 0 ? (
                <div className="text-sm text-slate-400">
                  The model returned no usable pairs. Try a different source or increase the pair count.
                </div>
              ) : (
                <div className="space-y-3">
                  {result.pairs.map((p, i) => (
                    <div
                      key={i}
                      className="border border-ink-800 rounded-md p-3 bg-ink-950"
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full border ${
                            CAT_COLORS[p.category] ||
                            "bg-slate-700/30 text-slate-300 border-slate-600/40"
                          }`}
                        >
                          {p.category}
                        </span>
                        <span className="text-xs text-slate-400">
                          difficulty: {p.difficulty}
                        </span>
                      </div>
                      <div className="font-medium text-slate-100">
                        Q: {p.question}
                      </div>
                      <div className="text-sm text-slate-300 mt-1">
                        A: {p.answer}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardBody>
          </Card>
        )}
      </div>
    </div>
  );
}
