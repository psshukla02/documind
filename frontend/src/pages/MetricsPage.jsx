import { useEffect, useState } from "react";
import { motion } from "framer-motion";

import PageHeader from "../components/PageHeader.jsx";
import PageTransition from "../components/PageTransition.jsx";
import Button from "../components/Button.jsx";
import { Card, CardBody, CardHeader } from "../components/Card.jsx";
import { api } from "../api/client.js";

function Stat({ label, value, hint, tint = "from-white to-white" }) {
  return (
    <motion.div
      whileHover={{ y: -2 }}
      className={`bg-gradient-to-b ${tint} border border-ink-100 rounded-2xl p-5 shadow-soft`}
    >
      <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-ink-500">
        {label}
      </div>
      <div className="text-3xl font-semibold text-ink-900 mt-1.5 tracking-tight">{value}</div>
      {hint && <div className="text-xs text-ink-500 mt-1.5">{hint}</div>}
    </motion.div>
  );
}

export default function MetricsPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const load = () => api.metrics().then(setData).catch((e) => setError(e.message));

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);

  if (error) return <div className="p-10 text-rose-500">{error}</div>;
  if (!data) return <div className="p-10 text-ink-500">Loading…</div>;

  return (
    <PageTransition>
      <div className="h-full flex flex-col overflow-hidden">
        <PageHeader
          kicker="Live · auto-refresh 5s"
          title="Metrics"
          subtitle="Observability for retrieval quality, latency, and usage across every endpoint."
          actions={<Button variant="ghost" onClick={load}>Refresh</Button>}
        />

        <div className="flex-1 overflow-y-auto px-10 pb-10 space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Stat
              label="Chat requests"
              value={data.counters.chat_requests ?? 0}
              hint={`avg ${data.chat.avg_latency_ms} ms`}
              tint="from-brand-50 to-white"
            />
            <Stat
              label="Ingestions"
              value={data.counters.ingest_requests ?? 0}
              hint={`avg ${data.ingest.avg_chunks} chunks/doc`}
              tint="from-mint-50 to-white"
            />
            <Stat
              label="Avg retrieval score"
              value={data.chat.avg_retrieval_score}
              hint="cosine similarity · higher is better"
              tint="from-lavender-50 to-white"
            />
            <Stat
              label="Errors"
              value={data.counters.errors ?? 0}
              hint={`uptime ${data.uptime_seconds}s`}
              tint="from-peach-50 to-white"
            />
          </div>

          <Card>
            <CardHeader>Recent Events</CardHeader>
            <CardBody>
              {data.recent_events.length === 0 ? (
                <div className="text-sm text-ink-500">No events yet.</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left">
                        <th className="py-2 pr-4 text-[11px] uppercase tracking-[0.14em] text-ink-500 font-semibold">Time</th>
                        <th className="py-2 pr-4 text-[11px] uppercase tracking-[0.14em] text-ink-500 font-semibold">Kind</th>
                        <th className="py-2 pr-4 text-[11px] uppercase tracking-[0.14em] text-ink-500 font-semibold">Latency</th>
                        <th className="py-2 pr-4 text-[11px] uppercase tracking-[0.14em] text-ink-500 font-semibold">Detail</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[...data.recent_events].reverse().map((e, i) => (
                        <tr key={i} className="border-t border-ink-100 hover:bg-ink-50/60 transition">
                          <td className="py-2.5 pr-4 text-ink-400 font-mono text-xs">
                            {new Date(e.ts * 1000).toLocaleTimeString()}
                          </td>
                          <td className="py-2.5 pr-4 text-ink-900 font-medium">{e.kind}</td>
                          <td className="py-2.5 pr-4 text-ink-700">{e.latency_ms?.toFixed?.(0)} ms</td>
                          <td className="py-2.5 pr-4 text-ink-500 font-mono text-xs truncate max-w-md">
                            {e.query || e.title || e.topic || ""}
                          </td>
                        </tr>
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
