import { motion } from "framer-motion";
import { Link } from "react-router-dom";

export default function Hero() {
  return (
    <section className="relative overflow-hidden">
      {/* Subtle backdrop blobs, pushed to the edges so they don't sit behind CTAs. */}
      <div
        aria-hidden
        className="absolute -top-32 -left-24 w-[420px] h-[420px] rounded-full blur-3xl opacity-40 pointer-events-none"
        style={{ background: "radial-gradient(closest-side, #dbe8ff, transparent)" }}
      />
      <div
        aria-hidden
        className="absolute -top-28 -right-24 w-[420px] h-[420px] rounded-full blur-3xl opacity-40 pointer-events-none"
        style={{ background: "radial-gradient(closest-side, #e9d5ff, transparent)" }}
      />

      <div className="relative max-w-5xl mx-auto px-8 pt-20 pb-14 text-center">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full
                     bg-white border border-ink-100
                     text-xs text-ink-700 shadow-soft"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-mint-500" />
          New · Autonomous Research Agent
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.05 }}
          className="mt-6 text-5xl md:text-6xl font-semibold tracking-tight text-ink-900 leading-[1.05]"
        >
          AI Technical Documentation
          <br />
          <span className="inline-block bg-clip-text text-transparent bg-gradient-to-r
                           from-indigo-600 via-fuchsia-500 to-rose-500
                           pb-2 -mb-2">
            Assistant
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.12 }}
          className="mt-6 text-lg md:text-xl text-ink-700 max-w-2xl mx-auto leading-relaxed"
        >
          Generate, understand, and enhance technical knowledge instantly —
          grounded in your own sources, with citations, confidence scoring,
          and an agent that grows your knowledge base on its own.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.2 }}
          className="mt-9 flex items-center justify-center gap-3 flex-wrap"
        >
          <Link
            to="/chat"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-full
                       text-white text-sm font-semibold
                       bg-brand-600 hover:bg-brand-700
                       shadow-lift transition-colors"
          >
            Start Chatting
            <span aria-hidden>→</span>
          </Link>
          <Link
            to="/agent"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-full
                       text-ink-900 text-sm font-semibold
                       bg-white border border-ink-200 hover:border-brand-300 hover:text-brand-700
                       shadow-soft transition-colors"
          >
            Try the Research Agent
            <span aria-hidden>→</span>
          </Link>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="mt-14 flex items-center justify-center gap-2 md:gap-3 flex-wrap text-xs text-ink-700"
        >
          <Pill>RAG · FAISS</Pill>
          <Pill>Citations + Confidence</Pill>
          <Pill>Synthetic Data</Pill>
          <Pill>Autonomous Agent</Pill>
        </motion.div>
      </div>
    </section>
  );
}

function Pill({ children }) {
  return (
    <span className="px-3 py-1 rounded-full bg-white border border-ink-100 shadow-soft">
      {children}
    </span>
  );
}
