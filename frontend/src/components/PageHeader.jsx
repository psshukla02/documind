import { motion } from "framer-motion";

export default function PageHeader({ title, subtitle, actions, kicker }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className="px-10 pt-10 pb-6 flex items-end justify-between gap-4"
    >
      <div>
        {kicker && (
          <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-brand-600 mb-1.5">
            {kicker}
          </div>
        )}
        <h1 className="text-3xl font-semibold tracking-tight text-ink-900">
          {title}
        </h1>
        {subtitle && (
          <p className="mt-1.5 text-[15px] text-ink-500 max-w-2xl leading-relaxed">
            {subtitle}
          </p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2 pb-1">{actions}</div>}
    </motion.div>
  );
}
