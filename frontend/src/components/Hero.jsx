import { motion } from "framer-motion";
import { Link } from "react-router-dom";

export default function Hero() {
  return (
    <section className="relative overflow-hidden">
      {/* soft gradient blobs */}
      <div
        className="absolute -top-40 -left-20 w-[520px] h-[520px] rounded-full blur-3xl opacity-60 pointer-events-none"
        style={{ background: "radial-gradient(closest-side, #dbe8ff, transparent)" }}
      />
      <div
        className="absolute -top-32 right-0 w-[520px] h-[520px] rounded-full blur-3xl opacity-60 pointer-events-none"
        style={{ background: "radial-gradient(closest-side, #e9d5ff, transparent)" }}
      />
      <div
        className="absolute top-40 left-1/2 -translate-x-1/2 w-[420px] h-[420px] rounded-full blur-3xl opacity-50 pointer-events-none"
        style={{ background: "radial-gradient(closest-side, #dcfce7, transparent)" }}
      />

      <div className="relative max-w-5xl mx-auto px-8 pt-20 pb-16 text-center">
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full
                     bg-white/70 backdrop-blur-xs border border-ink-100
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
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-brand-500 via-lavender-500 to-brand-400">
            Assistant
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.12 }}
          className="mt-5 text-lg md:text-xl text-ink-500 max-w-2xl mx-auto leading-relaxed"
        >
          Generate, understand, and enhance technical knowledge instantly —
          grounded in your own sources, with citations, confidence scoring,
          and an agent that grows your knowledge base on its own.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.2 }}
          className="mt-8 flex items-center justify-center gap-3"
        >
          <Link
            to="/chat"
            className="px-6 py-3 rounded-full text-white text-sm font-medium
                       bg-gradient-to-b from-brand-500 to-brand-600 hover:from-brand-400 hover:to-brand-500
                       shadow-soft transition"
          >
            Start Chatting
          </Link>
          <Link
            to="/agent"
            className="px-6 py-3 rounded-full text-ink-900 text-sm font-medium
                       bg-white/70 backdrop-blur-xs border border-ink-100 hover:bg-white transition"
          >
            Try the Research Agent →
          </Link>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="mt-14 flex items-center justify-center gap-8 text-xs text-ink-500"
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
    <span className="px-3 py-1 rounded-full bg-white/70 backdrop-blur-xs border border-ink-100">
      {children}
    </span>
  );
}
