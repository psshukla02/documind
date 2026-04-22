import { useEffect, useState } from "react";
import { motion } from "framer-motion";

import PageHeader from "../components/PageHeader.jsx";
import PageTransition from "../components/PageTransition.jsx";
import Button from "../components/Button.jsx";
import Spinner from "../components/Spinner.jsx";
import CopyButton from "../components/CopyButton.jsx";
import { Card, CardBody, CardHeader } from "../components/Card.jsx";
import { Input, Select } from "../components/Input.jsx";
import { api } from "../api/client.js";

const CAT_COLORS = {
  factual:   "bg-brand-50 text-brand-700 border-brand-100",
  reasoning: "bg-mint-50 text-mint-500 border-mint-100",
  edge_case: "bg-peach-50 text-peach-400 border-peach-100",
  example:   "bg-lavender-50 text-lavender-500 border-lavender-100",
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
    setError(null); setResult(null); setLoading(true);
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
    <PageTransition>
      <div className="h-full flex flex-col overflow-hidden">
        <PageHeader
          kicker="Diverse · JSON-safe"
          title="Synthetic Data Generator"
          subtitle="Generate diverse Q&A pairs from an ingested document. Output is strict JSON, copy-paste ready."
        />

        <div className="flex-1 overflow-y-auto px-10 pb-10 space-y-6">
          <Card>
            <CardHeader>Configuration</CardHeader>
            <CardBody>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs text-ink-500 mb-1.5">Source Document</label>
                  <Select value={docId} onChange={(e) => setDocId(e.target.value)}>
                    <option value="">(any — use first doc)</option>
                    {docs.map((d) => (
                      <option key={d.doc_id} value={d.doc_id}>
                        {d.title} ({d.chunks} chunks)
                      </option>
                    ))}
                  </Select>
                </div>
                <div>
                  <label className="block text-xs text-ink-500 mb-1.5">Number of Pairs</label>
                  <Input
                    type="number"
                    min={1} max={20}
                    value={nPairs}
                    onChange={(e) => setNPairs(Number(e.target.value))}
                  />
                </div>
                <div className="flex items-end">
                  <Button onClick={run} disabled={loading || docs.length === 0}>
                    {loading ? "Generating…" : "Generate"}
                  </Button>
                </div>
              </div>
              {docs.length === 0 && (
                <div className="mt-3 text-sm text-peach-400">
                  Knowledge base is empty — ingest a document or use the Research Agent first.
                </div>
              )}
              {error && <div className="mt-3 text-sm text-rose-500">{error}</div>}
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
                  <div className="flex items-center gap-3 text-xs text-ink-500 font-normal">
                    <span>{result.latency_ms?.toFixed?.(0)} ms</span>
                    <CopyButton text={JSON.stringify(result.pairs, null, 2)} label="Copy JSON" />
                  </div>
                </div>
              </CardHeader>
              <CardBody>
                {result.pairs.length === 0 ? (
                  <div className="text-sm text-ink-500">
                    The model returned no usable pairs. Try a different source or increase the pair count.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {result.pairs.map((p, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 6 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.03 }}
                        className="rounded-2xl border border-ink-100 p-4 bg-white hover:shadow-soft transition"
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <span className={[
                            "text-[11px] px-2 py-0.5 rounded-full border font-medium",
                            CAT_COLORS[p.category] || "bg-ink-50 text-ink-500 border-ink-100",
                          ].join(" ")}>
                            {p.category}
                          </span>
                          <span className="text-[11px] text-ink-400">difficulty: {p.difficulty}</span>
                        </div>
                        <div className="font-medium text-ink-900">Q: {p.question}</div>
                        <div className="text-sm text-ink-700 mt-1 leading-relaxed">A: {p.answer}</div>
                      </motion.div>
                    ))}
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
