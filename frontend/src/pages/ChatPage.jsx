import { useRef, useState, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";

import PageHeader from "../components/PageHeader.jsx";
import PageTransition from "../components/PageTransition.jsx";
import Button from "../components/Button.jsx";
import Spinner, { Typing } from "../components/Spinner.jsx";
import CopyButton from "../components/CopyButton.jsx";
import Markdown from "../components/Markdown.jsx";
import { Card, CardBody, SectionLabel } from "../components/Card.jsx";
import { Input } from "../components/Input.jsx";
import { api } from "../api/client.js";

function ConfidenceBar({ value = 0 }) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  const color = pct > 70 ? "bg-mint-500" : pct > 40 ? "bg-peach-400" : "bg-rose-400";
  return (
    <div className="flex items-center gap-2">
      <div className="w-28 h-1 bg-ink-100 rounded-full overflow-hidden">
        <motion.div
          className={`h-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>
      <span className="text-xs text-ink-500">{pct.toFixed(0)}%</span>
    </div>
  );
}

function UserBubble({ text }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex justify-end"
    >
      <div className="max-w-2xl rounded-3xl rounded-br-lg px-5 py-3 text-[15px]
                      bg-gradient-to-b from-brand-500 to-brand-600 text-white
                      shadow-soft">
        {text}
      </div>
    </motion.div>
  );
}

function AssistantBubble({ m }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className="flex justify-start"
    >
      <Card className="max-w-3xl w-full rounded-3xl rounded-bl-lg">
        <CardBody className="p-5">
          <Markdown>{m.content}</Markdown>

          {m.citations?.length > 0 && (
            <div className="mt-5 pt-4 border-t border-ink-100">
              <SectionLabel>Sources</SectionLabel>
              <ul className="mt-2 space-y-1.5 text-sm">
                {m.citations.map((c) => (
                  <li key={c.id} className="flex items-center gap-2">
                    <span className="cite-chip">{c.id}</span>
                    <a
                      href={c.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-brand-600 hover:underline truncate"
                    >
                      {c.title}
                    </a>
                    <span className="text-xs text-ink-500 ml-auto">score {c.score}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="mt-4 pt-3 border-t border-ink-100 flex items-center justify-between text-xs text-ink-500">
            <div className="flex items-center gap-5">
              <div className="flex items-center gap-2">
                <span>Confidence</span>
                <ConfidenceBar value={m.confidence ?? 0} />
              </div>
              <div>Latency: {m.latency_ms?.toFixed?.(0) ?? m.latency_ms} ms</div>
              {m.tokens != null && <div>Tokens: {m.tokens}</div>}
            </div>
            <CopyButton text={m.content} />
          </div>
        </CardBody>
      </Card>
    </motion.div>
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
    <PageTransition>
      <div className="h-full flex flex-col">
        <PageHeader
          kicker="Grounded · Cited · Scored"
          title="Chat"
          subtitle="Ask technical questions — every answer is grounded in your knowledge base, with inline citations and confidence."
        />

        <div className="flex-1 overflow-y-auto px-10 py-6 space-y-5">
          {messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
            >
              <Card className="bg-gradient-to-b from-brand-50 to-white">
                <CardBody className="p-6">
                  <SectionLabel>Get started</SectionLabel>
                  <div className="mt-2 text-ink-900 text-[15px]">
                    Try one of these, or ingest something in the{" "}
                    <span className="text-brand-600 font-medium">Knowledge Base</span>:
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {EXAMPLE_QUERIES.map((q) => (
                      <motion.button
                        key={q}
                        onClick={() => send(q)}
                        whileHover={{ y: -1 }}
                        whileTap={{ scale: 0.97 }}
                        className="px-3.5 py-1.5 text-sm rounded-full bg-white border border-ink-100
                                   text-ink-700 shadow-soft hover:border-brand-200 hover:text-ink-900 transition"
                      >
                        {q}
                      </motion.button>
                    ))}
                  </div>
                </CardBody>
              </Card>
            </motion.div>
          )}

          <AnimatePresence initial={false}>
            {messages.map((m, i) =>
              m.role === "user" ? (
                <UserBubble key={i} text={m.content} />
              ) : (
                <AssistantBubble key={i} m={m} />
              )
            )}
          </AnimatePresence>

          {loading && (
            <div className="flex justify-start">
              <Card className="rounded-3xl rounded-bl-lg">
                <CardBody className="p-3">
                  <Typing />
                </CardBody>
              </Card>
            </div>
          )}

          <div ref={endRef} />
        </div>

        {error && (
          <div className="px-10 py-2 text-sm text-rose-600 border-t border-ink-100 bg-rose-50/50">
            {error}
          </div>
        )}

        <form
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
          className="sticky bottom-0 px-10 py-4 border-t border-ink-100 glass flex gap-2"
        >
          <Input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything about your documents…"
            disabled={loading}
          />
          <Button type="submit" disabled={loading}>
            {loading ? <Spinner /> : "Send"}
          </Button>
        </form>
      </div>
    </PageTransition>
  );
}
