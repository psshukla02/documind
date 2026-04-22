import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import Hero from "../components/Hero.jsx";
import { Card, CardBody, SectionLabel } from "../components/Card.jsx";
import PageTransition from "../components/PageTransition.jsx";

const FEATURES = [
  {
    title: "Grounded Chat",
    body: "Ask anything. Every answer cites the source, shows confidence, and links back to the chunk it came from.",
    icon: "💬",
    to: "/chat",
    tint: "from-brand-50 to-white",
  },
  {
    title: "Research Agent",
    body: "Give it a topic — no URL needed. It plans queries, crawls the web, judges relevance, and grows your KB live.",
    icon: "🤖",
    to: "/agent",
    tint: "from-lavender-50 to-white",
  },
  {
    title: "Doc Generator",
    body: "Publication-quality Markdown docs from a topic or a snippet, optionally grounded in your knowledge base.",
    icon: "📝",
    to: "/docs-gen",
    tint: "from-mint-50 to-white",
  },
  {
    title: "Synthetic Data",
    body: "Generate diverse Q&A pairs (factual, reasoning, edge-case) with a strict JSON schema, copy-paste ready.",
    icon: "🧪",
    to: "/synthetic",
    tint: "from-peach-50 to-white",
  },
];

export default function HomePage() {
  return (
    <PageTransition>
      <div className="h-full overflow-y-auto">
        <Hero />

        <motion.section
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-10%" }}
          transition={{ duration: 0.5 }}
          className="max-w-6xl mx-auto px-8 pb-20"
        >
          <div className="text-center mb-10">
            <SectionLabel>Modules</SectionLabel>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight text-ink-900">
              Four capabilities, one place
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {FEATURES.map((f, i) => (
              <motion.div
                key={f.to}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.06 }}
              >
                <Link to={f.to} className="block">
                  <Card interactive className={`h-full bg-gradient-to-b ${f.tint}`}>
                    <CardBody className="p-6">
                      <div className="text-3xl mb-3">{f.icon}</div>
                      <div className="text-lg font-semibold text-ink-900 tracking-tight">
                        {f.title}
                      </div>
                      <p className="mt-1.5 text-[15px] text-ink-500 leading-relaxed">
                        {f.body}
                      </p>
                      <div className="mt-4 text-sm font-medium text-brand-600">
                        Open →
                      </div>
                    </CardBody>
                  </Card>
                </Link>
              </motion.div>
            ))}
          </div>
        </motion.section>
      </div>
    </PageTransition>
  );
}
