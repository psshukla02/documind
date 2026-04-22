import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

import PageHeader from "../components/PageHeader.jsx";
import PageTransition from "../components/PageTransition.jsx";
import Button from "../components/Button.jsx";
import Spinner from "../components/Spinner.jsx";
import { Card, CardBody, CardHeader, SectionLabel } from "../components/Card.jsx";
import { Input } from "../components/Input.jsx";
import { API_BASE } from "../api/client.js";

const EVENT_STYLE = {
  start:          { color: "text-ink-900",  dot: "bg-ink-300" },
  plan:           { color: "text-brand-600", dot: "bg-brand-400" },
  search_start:   { color: "text-lavender-500", dot: "bg-lavender-400" },
  search_results: { color: "text-lavender-500", dot: "bg-lavender-400" },
  scrape_start:   { color: "text-ink-700",  dot: "bg-ink-300" },
  scrape_done:    { color: "text-ink-900",  dot: "bg-ink-400" },
  scrape_failed:  { color: "text-peach-400", dot: "bg-peach-400" },
  judge:          { color: "text-lavender-500", dot: "bg-lavender-500" },
  ingest:         { color: "text-mint-500", dot: "bg-mint-500" },
  ingest_failed:  { color: "text-rose-500", dot: "bg-rose-500" },
  skip:           { color: "text-ink-400",  dot: "bg-ink-200" },
  done:           { color: "text-mint-500", dot: "bg-mint-500" },
  error:          { color: "text-rose-500", dot: "bg-rose-500" },
};

function EventRow({ e }) {
  const style = EVENT_STYLE[e.type] || { color: "text-ink-500", dot: "bg-ink-300" };
  const ts = new Date(e.ts * 1000).toLocaleTimeString();

  let detail;
  switch (e.type) {
    case "start":
      detail = <>Researching <b className="text-ink-900">{e.topic}</b> · {e.num_queries} queries × {e.per_query} results</>;
      break;
    case "plan":
      detail = (
        <div>
          <div>Planned queries:</div>
          <ul className="mt-1.5 space-y-0.5">
            {e.queries.map((q, i) => (
              <li key={i} className="font-mono text-xs text-ink-700">· {q}</li>
            ))}
          </ul>
        </div>
      );
      break;
    case "search_start":
      detail = <>Searching: <span className="font-mono text-xs">{e.query}</span></>;
      break;
    case "search_results":
      detail = <>Found {e.urls.length} results for <span className="font-mono text-xs">{e.query}</span></>;
      break;
    case "scrape_start":
      detail = <>Scraping <span className="text-ink-900">{e.title || e.url}</span></>;
      break;
    case "scrape_done":
      detail = (
        <>
          Scraped {e.chars.toLocaleString()} chars —{" "}
          <a href={e.url} target="_blank" rel="noreferrer" className="text-brand-600 hover:underline">
            {e.title || e.url}
          </a>
        </>
      );
      break;
    case "scrape_failed":
      detail = <>Scrape failed: {e.url} <span className="text-ink-400">({e.reason})</span></>;
      break;
    case "judge":
      detail = (
        <>
          <b className={e.decision === "keep" ? "text-mint-500" : "text-ink-500"}>
            {e.decision.toUpperCase()}
          </b>{" "}
          — {e.reason} <span className="text-ink-400 text-xs">({e.url})</span>
        </>
      );
      break;
    case "ingest":
      detail = <>Ingested <b className="text-ink-900">{e.title}</b> <span className="text-ink-500">({e.chunks} chunks)</span></>;
      break;
    case "ingest_failed":
      detail = <>Ingest failed: {e.url} — {e.reason}</>;
      break;
    case "skip":
      detail = <span className="text-ink-400">Skipped {e.url} · {e.reason}</span>;
      break;
    case "done":
      detail = (
        <>
          Done — {e.summary.ingested} docs ingested, {e.summary.total_chunks} chunks added
          in {Math.round(e.summary.elapsed_ms)} ms
        </>
      );
      break;
    case "error":
      detail = <span className="text-rose-500">{e.message}</span>;
      break;
    default:
      detail = <span className="text-ink-400">{JSON.stringify(e)}</span>;
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.25 }}
      className="flex gap-3 py-2 border-b border-ink-100/70 last:border-b-0 text-sm"
    >
      <span className={`mt-2 inline-block w-1.5 h-1.5 rounded-full shrink-0 ${style.dot}`} />
      <span className="text-ink-400 font-mono text-[11px] w-20 shrink-0 pt-0.5">{ts}</span>
      <div className={`flex-1 ${style.color}`}>{detail}</div>
    </motion.div>
  );
}

function Stat({ label, value, accent }) {
  const colors = {
    emerald: "text-mint-500",
    brand:   "text-brand-600",
    default: "text-ink-900",
  };
  return (
    <div className="rounded-2xl bg-white border border-ink-100 p-4 shadow-soft">
      <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-ink-500">
        {label}
      </div>
      <div className={`text-2xl font-semibold mt-1 tracking-tight ${colors[accent] || colors.default}`}>
        {value}
      </div>
    </div>
  );
}

function Summary({ summary }) {
  return (
    <Card>
      <CardHeader>Research Summary</CardHeader>
      <CardBody>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
          <Stat label="Queries"       value={summary.queries.length} />
          <Stat label="Pages scraped" value={summary.scraped} />
          <Stat label="Docs ingested" value={summary.ingested} accent="emerald" />
          <Stat label="Chunks added"  value={summary.total_chunks} accent="brand" />
        </div>

        {summary.documents.length > 0 ? (
          <ul className="space-y-1.5 text-sm">
            {summary.documents.map((d, i) => (
              <li key={i} className="flex items-center gap-2">
                <span className="cite-chip">✓</span>
                <a href={d.url} target="_blank" rel="noreferrer" className="text-brand-600 hover:underline truncate">
                  {d.title}
                </a>
                <span className="text-xs text-ink-400 ml-auto">{d.chunks} chunks</span>
              </li>
            ))}
          </ul>
        ) : (
          <div className="text-sm text-ink-500">
            Nothing ingested this run. Try a broader topic or increase results per query.
          </div>
        )}
      </CardBody>
    </Card>
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

  useEffect(() => () => esRef.current?.close(), []);

  const start = (explicit) => {
    const t = (explicit ?? topic).trim();
    if (!t) {
      setError("Enter a topic to research.");
      return;
    }
    setError(null);
    setEvents([]);
    setSummary(null);
    setRunning(true);
    esRef.current?.close();

    const url = `${API_BASE}/agent/stream?topic=${encodeURIComponent(t)}&num_queries=${numQueries}&per_query=${perQuery}`;
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
      } catch { /* ignore keepalive */ }
    };

    es.onerror = () => {
      setRunning((was) => {
        if (was && !summary) setError("Connection to agent stream lost.");
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
    <PageTransition>
      <div className="h-full flex flex-col overflow-hidden">
        <PageHeader
          kicker="No URL needed"
          title="Research Agent"
          subtitle="Give it a topic. It plans queries, crawls the web, judges relevance, and grows your knowledge base — live."
        />

        <div className="flex-1 overflow-y-auto px-10 pb-10 space-y-6">
          <Card>
            <CardHeader>Start a research run</CardHeader>
            <CardBody>
              <div className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder='Topic, e.g. "FastAPI dependency injection"'
                    disabled={running}
                    onKeyDown={(e) => e.key === "Enter" && !running && start()}
                  />
                  {running ? (
                    <Button variant="danger" onClick={stop}>Stop</Button>
                  ) : (
                    <Button onClick={() => start()}>Start</Button>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center justify-between text-xs text-ink-500">
                      <span>Search queries</span>
                      <span className="font-mono text-ink-900">{numQueries}</span>
                    </div>
                    <input
                      type="range" min={1} max={5}
                      value={numQueries}
                      onChange={(e) => setNumQueries(Number(e.target.value))}
                      disabled={running}
                      className="w-full mt-2 accent-brand-500"
                    />
                  </div>
                  <div>
                    <div className="flex items-center justify-between text-xs text-ink-500">
                      <span>Results per query</span>
                      <span className="font-mono text-ink-900">{perQuery}</span>
                    </div>
                    <input
                      type="range" min={1} max={5}
                      value={perQuery}
                      onChange={(e) => setPerQuery(Number(e.target.value))}
                      disabled={running}
                      className="w-full mt-2 accent-brand-500"
                    />
                  </div>
                </div>

                {!running && events.length === 0 && (
                  <div className="pt-2">
                    <SectionLabel>Try</SectionLabel>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {EXAMPLE_TOPICS.map((t) => (
                        <motion.button
                          key={t}
                          onClick={() => start(t)}
                          whileHover={{ y: -1 }}
                          whileTap={{ scale: 0.97 }}
                          className="px-3.5 py-1.5 text-xs rounded-full bg-white border border-ink-100 text-ink-700 shadow-soft hover:border-brand-200 hover:text-ink-900 transition"
                        >
                          {t}
                        </motion.button>
                      ))}
                    </div>
                  </div>
                )}

                {error && <div className="text-sm text-rose-500">{error}</div>}
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
                  <div className="text-sm text-ink-500">Waiting for first event…</div>
                ) : (
                  <div className="max-h-[500px] overflow-y-auto pr-1">
                    <AnimatePresence initial={false}>
                      {events.map((e, i) => (
                        <EventRow key={i} e={e} />
                      ))}
                    </AnimatePresence>
                    <div ref={logEndRef} />
                  </div>
                )}
              </CardBody>
            </Card>
          )}

          {summary && <Summary summary={summary} />}
        </div>
      </div>
    </PageTransition>
  );
}
