import { useRef, useState, useEffect } from "react";
import PageHeader from "../components/PageHeader.jsx";
import Button from "../components/Button.jsx";
import Spinner from "../components/Spinner.jsx";
import CopyButton from "../components/CopyButton.jsx";
import Markdown from "../components/Markdown.jsx";
import { Card, CardBody } from "../components/Card.jsx";
import { api } from "../api/client.js";

function ConfidenceBar({ value }) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  const color =
    pct > 70 ? "bg-emerald-500" : pct > 40 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="w-32 h-1.5 bg-ink-800 rounded-full overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-400">{pct.toFixed(0)}%</span>
    </div>
  );
}

function MessageBubble({ m }) {
  if (m.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-2xl bg-brand-600 text-white rounded-lg px-4 py-2 text-sm">
          {m.content}
        </div>
      </div>
    );
  }
  return (
    <div className="flex justify-start">
      <Card className="max-w-3xl w-full">
        <CardBody>
          <Markdown>{m.content}</Markdown>

          {m.citations && m.citations.length > 0 && (
            <div className="mt-4 pt-3 border-t border-ink-800">
              <div className="text-xs uppercase tracking-wider text-slate-400 mb-2">
                Sources
              </div>
              <ul className="space-y-1 text-sm">
                {m.citations.map((c) => (
                  <li key={c.id} className="flex items-center gap-2">
                    <span className="cite-chip">{c.id}</span>
                    <a
                      href={c.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-brand-400 hover:underline truncate"
                    >
                      {c.title}
                    </a>
                    <span className="text-xs text-slate-500 ml-auto">
                      score {c.score}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span>Confidence:</span>
                <ConfidenceBar value={m.confidence ?? 0} />
              </div>
              <div>Latency: {m.latency_ms?.toFixed?.(0) ?? m.latency_ms} ms</div>
              {m.tokens != null && <div>Tokens: {m.tokens}</div>}
            </div>
            <CopyButton text={m.content} />
          </div>
        </CardBody>
      </Card>
    </div>
  );
}

const EXAMPLE_QUERIES = [
  "What is FastAPI and what does it do?",
  "How do I define a Pydantic model?",
  "What happens if I ingest a non-existent URL?",
];

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async (q) => {
    const query = (q ?? input).trim();
    if (!query) {
      setError("Please type a question.");
      return;
    }
    setError(null);
    setInput("");
    setMessages((m) => [...m, { role: "user", content: query }]);
    setLoading(true);
    try {
      const res = await api.chat(query);
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: res.answer,
          citations: res.citations,
          confidence: res.confidence,
          latency_ms: res.latency_ms,
          tokens: res.tokens,
        },
      ]);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col">
      <PageHeader
        title="Chat"
        subtitle="Ask technical questions grounded in your knowledge base"
      />

      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-4">
        {messages.length === 0 && (
          <Card>
            <CardBody>
              <div className="text-slate-300 mb-3">
                👋 Welcome. Try one of these, or ingest something under{" "}
                <span className="text-brand-400">Knowledge Base</span>:
              </div>
              <div className="flex flex-wrap gap-2">
                {EXAMPLE_QUERIES.map((q) => (
                  <button
                    key={q}
                    onClick={() => send(q)}
                    className="px-3 py-1.5 text-sm rounded-full border border-ink-800 text-slate-300 hover:bg-ink-800"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </CardBody>
          </Card>
        )}

        {messages.map((m, i) => (
          <MessageBubble key={i} m={m} />
        ))}

        {loading && (
          <div className="flex justify-start">
            <Card>
              <CardBody>
                <Spinner label="Retrieving context and generating answer…" />
              </CardBody>
            </Card>
          </div>
        )}

        <div ref={endRef} />
      </div>

      {error && (
        <div className="px-8 py-2 text-sm text-red-400 border-t border-ink-800 bg-red-950/30">
          {error}
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
        className="border-t border-ink-800 px-8 py-4 flex gap-2 bg-ink-900/40"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask anything about the documents in your knowledge base…"
          className="flex-1 bg-ink-900 border border-ink-800 rounded-md px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-brand-500"
        />
        <Button type="submit" disabled={loading}>
          {loading ? "Sending…" : "Send"}
        </Button>
      </form>
    </div>
  );
}
