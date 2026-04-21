import { useEffect, useState } from "react";
import PageHeader from "../components/PageHeader.jsx";
import Button from "../components/Button.jsx";
import { Card, CardBody, CardHeader } from "../components/Card.jsx";
import { api } from "../api/client.js";

function Stat({ label, value, hint }) {
  return (
    <Card>
      <CardBody>
        <div className="text-xs uppercase tracking-wider text-slate-400">{label}</div>
        <div className="text-2xl font-semibold text-white mt-1">{value}</div>
        {hint && <div className="text-xs text-slate-500 mt-1">{hint}</div>}
      </CardBody>
    </Card>
  );
}

export default function MetricsPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const load = () => {
    api.metrics().then(setData).catch((e) => setError(e.message));
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, []);

  if (error) return <div className="p-8 text-red-400">{error}</div>;
  if (!data) return <div className="p-8 text-slate-400">Loading…</div>;

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <PageHeader
        title="Metrics"
        subtitle="Observability for retrieval quality, latency, and usage"
        actions={
          <Button variant="ghost" onClick={load}>
            Refresh
          </Button>
        }
      />
      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Stat
            label="Chat requests"
            value={data.counters.chat_requests ?? 0}
            hint={`avg ${data.chat.avg_latency_ms} ms`}
          />
          <Stat
            label="Ingestions"
            value={data.counters.ingest_requests ?? 0}
            hint={`avg ${data.ingest.avg_chunks} chunks/doc`}
          />
          <Stat
            label="Avg retrieval score"
            value={data.chat.avg_retrieval_score}
            hint="cosine similarity · higher is better"
          />
          <Stat
            label="Errors"
            value={data.counters.errors ?? 0}
            hint={`uptime ${data.uptime_seconds}s`}
          />
        </div>

        <Card>
          <CardHeader>Recent Events</CardHeader>
          <CardBody>
            {data.recent_events.length === 0 ? (
              <div className="text-sm text-slate-400">No events yet.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="text-left text-slate-400 border-b border-ink-800">
                    <tr>
                      <th className="py-2 pr-4">Time</th>
                      <th className="py-2 pr-4">Kind</th>
                      <th className="py-2 pr-4">Latency</th>
                      <th className="py-2 pr-4">Detail</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...data.recent_events].reverse().map((e, i) => (
                      <tr key={i} className="border-b border-ink-800/60">
                        <td className="py-2 pr-4 text-slate-400 font-mono text-xs">
                          {new Date(e.ts * 1000).toLocaleTimeString()}
                        </td>
                        <td className="py-2 pr-4 text-slate-200">{e.kind}</td>
                        <td className="py-2 pr-4 text-slate-300">
                          {e.latency_ms?.toFixed?.(0)} ms
                        </td>
                        <td className="py-2 pr-4 text-slate-400 font-mono text-xs truncate max-w-md">
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
  );
}
