import { useEffect, useRef, useState } from "react";
import PageHeader from "../components/PageHeader.jsx";
import Button from "../components/Button.jsx";
import Spinner from "../components/Spinner.jsx";
import { Card, CardBody, CardHeader } from "../components/Card.jsx";

const EVENT_STYLE = {
  start: { icon: "🚀", color: "text-slate-200" },
  plan: { icon: "🧭", color: "text-brand-400" },
  search_start: { icon: "🔎", color: "text-sky-300" },
  search_results: { icon: "📋", color: "text-sky-200" },
  scrape_start: { icon: "⬇️", color: "text-slate-300" },
  scrape_done: { icon: "📄", color: "text-slate-200" },
  scrape_failed: { icon: "⚠️", color: "text-amber-400" },
  judge: { icon: "⚖️", color: "text-violet-300" },
  ingest: { icon: "✅", color: "text-emerald-400" },
  ingest_failed: { icon: "❌", color: "text-red-400" },
  skip: { icon: "⏭️", color: "text-slate-500" },
  done: { icon: "🏁", color: "text-emerald-400" },
  error: { icon: "🔥", color: "text-red-400" },
};

function EventRow({ e }) {
  const style = EVENT_STYLE[e.type] || { icon: "•", color: "text-slate-400" };
  const ts = new Date(e.ts * 1000).toLocaleTimeString();

  let detail = null;
  switch (e.type) {
    case "start":
      detail = (
        <span>
          Researching <b className="text-white">{e.topic}</b> · {e.num_queries}{" "}
          queries × {e.per_query} results
        </span>
      );
      break;
    case "plan":
      detail = (
        <div>
          <div>Planned queries:</div>
          <ul className="list-disc list-inside text-slate-300 text-sm mt-1">
            {e.queries.map((q, i) => (
              <li key={i}>
                <span className="font-mono text-xs">{q}</span>
              </li>
            ))}
          </ul>
        </div>
      );
      break;
    case "search_start":
      detail = (
        <span>
          Searching: <span className="font-mono text-xs">{e.query}</span>
        </span>
      );
      break;
    case "search_results":
      detail = (
        <span>
          Found {e.urls.length} results for{" "}
          <span className="font-mono text-xs">{e.query}</span>
        </span>
      );
      break;
    case "scrape_start":
      detail = (
        <span>
          Scraping <span className="text-slate-200">{e.title || e.url}</span>
        </span>
      );
      break;
    case "scrape_done":
      detail = (
        <span>
          Scraped {e.chars.toLocaleString()} chars:{" "}
          <a href={e.url} target="_blank" rel="noreferrer" className="text-brand-400 hover:underline">
            {e.title || e.url}
          </a>
        </span>
      );
      break;
    case "scrape_failed":
      detail = (
        <span>
          Scrape failed: {e.url} <span className="text-slate-500">({e.reason})</span>
        </span>
      );
      break;
    case "judge":
      detail = (
        <span>
          <b className={e.decision === "keep" ? "text-emerald-400" : "text-slate-400"}>
            {e.decision.toUpperCase()}
          </b>{" "}
          — {e.reason} <span className="text-slate-500 text-xs">({e.url})</span>
        </span>
      );
      break;
    case "ingest":
      detail = (
        <span>
          Ingested <b className="text-white">{e.title}</b>{" "}
          <span className="text-slate-400">({e.chunks} chunks)</span>
        </span>
      );
      break;
    case "ingest_failed":
      detail = <span>Ingest failed: {e.url} — {e.reason}</span>;
      break;
    case "skip":
      detail = (
        <span className="text-slate-500">
          Skipped {e.url} ({e.reason})
        </span>
      );
      break;
    case "done":
      detail = (
        <span>
          Done — {e.summary.ingested} docs ingested, {e.summary.total_chunks}{" "}
          chunks added in {Math.round(e.summary.elapsed_ms)} ms
        </span>
      );
      break;
    case "error":
      detail = <span className="text-red-400">{e.message}</span>;
      break;
    default:
      detail = <span className="text-slate-500">{JSON.stringify(e)}</span>;
  }

  return (
    <div className="flex gap-3 py-1.5 border-b border-ink-800/60 text-sm">
      <span className="shrink-0">{style.icon}</span>
      <span className="text-slate-500 font-mono text-xs shrink-0 w-20">{ts}</span>
      <div className={`flex-1 ${style.color}`}>{detail}</div>
    </div>
  );
}

function Summary({ summary }) {
  return (
    <Card>
      <CardHeader>Research Summary</CardHeader>
      <CardBody>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <Stat label="Queries" value={summary.queries.length} />
          <Stat label="Pages scraped" value={summary.scraped} />
          <Stat label="Docs ingested" value={summary.ingested} accent="emerald" />
          <Stat label="Chunks added" value={summary.total_chunks} accent="brand" />
        </div>
        {summary.documents.length > 0 ? (
          <ul className="space-y-1 text-sm">
            {summary.documents.map((d, i) => (
              <li key={i} className="flex items-center gap-2">
                <span className="cite-chip">✓</span>
                <a
                  href={d.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-brand-400 hover:underline truncate"
                >
                  {d.title}
                </a>
                <span className="text-xs text-slate-500 ml-auto">
                  {d.chunks} chunks
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <div className="text-sm text-slate-400">
            Nothing ingested this run. Try a broader topic or increase results per query.
          </div>
        )}
      </CardBody>
    </Card>
  );
}

function Stat({ label, value, accent }) {
  const color =
    accent === "emerald"
      ? "text-emerald-400"
      : accent === "brand"
      ? "text-brand-400"
      : "text-white";
  return (
    <div className="bg-ink-950 border border-ink-800 rounded-md p-3">
      <div className="text-xs uppercase tracking-wider text-slate-400">{label}</div>
      <div className={`text-2xl font-semibold mt-0.5 ${color}`}>{value}</div>
    </div>
  );
}

const EXAMPLE_TOPICS = [
  "FastAPI dependency injection",
  "Pydantic v2 validators",
  "React hooks rules",
  "Tailwind utility-first CSS",
];

export default function AgentPage() {
  const [topic, setTopic] = useState("");
  const [numQueries, setNumQueries] = useState(3);
  const [perQuery, setPerQuery] = useState(3);
  const [events, setEvents] = useState([]);
  const [running, setRunning] = useState(false);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);
  const esRef = useRef(null);
  const logEndRef = useRef(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  useEffect(() => {
    return () => esRef.current?.close();
  }, []);

  const start = (explicitTopic) => {
    const t = (explicitTopic ?? topic).trim();
    if (!t) {
      setError("Enter a topic to research.");
      return;
    }
    setError(null);
    setEvents([]);
    setSummary(null);
    setRunning(true);
    esRef.current?.close();

    const url = `/api/agent/stream?topic=${encodeURIComponent(t)}&num_queries=${numQueries}&per_query=${perQuery}`;
    const es = new EventSource(url);
    esRef.current = es;

    es.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        setEvents((prev) => [...prev, data]);
        if (data.type === "done") {
          setSummary(data.summary);
          setRunning(false);
          es.close();
        }
        if (data.type === "error" && !data.ts) {
          setError(data.message);
          setRunning(false);
          es.close();
        }
      } catch (e) {
        // Non-JSON keepalive; ignore.
      }
    };

    es.onerror = () => {
      // EventSource fires onerror on normal close too — only report
      // if we never got a "done" event.
      setRunning((wasRunning) => {
        if (wasRunning && !summary) {
          setError("Connection to agent stream lost.");
        }
        return false;
      });
      es.close();
    };
  };

  const stop = () => {
    esRef.current?.close();
    setRunning(false);
  };

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <PageHeader
        title="Research Agent"
        subtitle="Autonomously search the web, judge relevance, and grow the knowledge base"
      />
      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6">
        <Card>
          <CardHeader>Start a research run</CardHeader>
          <CardBody>
            <div className="space-y-3">
              <div className="flex gap-2">
                <input
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder='Topic to research, e.g. "FastAPI dependency injection"'
                  className="flex-1 bg-ink-900 border border-ink-800 rounded-md px-3 py-2 text-sm"
                  disabled={running}
                  onKeyDown={(e) => e.key === "Enter" && !running && start()}
                />
                {running ? (
                  <Button variant="danger" onClick={stop}>
                    Stop
                  </Button>
                ) : (
                  <Button onClick={() => start()}>Start Research</Button>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <label className="block text-xs text-slate-400">
                  Search queries: {numQueries}
                  <input
                    type="range"
                    min={1}
                    max={5}
                    value={numQueries}
                    onChange={(e) => setNumQueries(Number(e.target.value))}
                    disabled={running}
                    className="w-full mt-1 accent-brand-500"
                  />
                </label>
                <label className="block text-xs text-slate-400">
                  Results per query: {perQuery}
                  <input
                    type="range"
                    min={1}
                    max={5}
                    value={perQuery}
                    onChange={(e) => setPerQuery(Number(e.target.value))}
                    disabled={running}
                    className="w-full mt-1 accent-brand-500"
                  />
                </label>
              </div>

              {!running && events.length === 0 && (
                <div className="pt-2">
                  <div className="text-xs text-slate-400 mb-2">Try:</div>
                  <div className="flex flex-wrap gap-2">
                    {EXAMPLE_TOPICS.map((t) => (
                      <button
                        key={t}
                        onClick={() => start(t)}
                        className="px-3 py-1 text-xs rounded-full border border-ink-800 text-slate-300 hover:bg-ink-800"
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {error && <div className="text-sm text-red-400">{error}</div>}
            </div>
          </CardBody>
        </Card>

        {(running || events.length > 0) && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <span>Live Timeline</span>
                {running && <Spinner label="Agent working…" />}
              </div>
            </CardHeader>
            <CardBody>
              {events.length === 0 ? (
                <div className="text-sm text-slate-400">Waiting for first event…</div>
              ) : (
                <div className="max-h-[500px] overflow-y-auto pr-1">
                  {events.map((e, i) => (
                    <EventRow key={i} e={e} />
                  ))}
                  <div ref={logEndRef} />
                </div>
              )}
            </CardBody>
          </Card>
        )}

        {summary && <Summary summary={summary} />}
      </div>
    </div>
  );
}
