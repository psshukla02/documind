import { motion } from "framer-motion";

export function Card({ children, className = "", interactive = false, as = "div" }) {
  const Tag = interactive ? motion.div : motion.div;
  const hoverProps = interactive
    ? {
        whileHover: { y: -2, boxShadow: "0 10px 30px -12px rgba(16,24,40,0.15), 0 4px 10px -4px rgba(16,24,40,0.08)" },
        transition: { type: "spring", stiffness: 300, damping: 24 },
      }
    : {};
  return (
    <Tag
      {...hoverProps}
      className={[
        "bg-white border border-ink-100 rounded-2xl shadow-soft",
        interactive ? "cursor-pointer" : "",
        className,
      ].join(" ")}
    >
      {children}
    </Tag>
  );
}

export function CardHeader({ children, className = "" }) {
  return (
    <div
      className={[
        "px-5 py-4 border-b border-ink-100",
        "text-ink-900 font-semibold tracking-tight",
        className,
      ].join(" ")}
    >
      {children}
    </div>
  );
}

export function CardBody({ children, className = "" }) {
  return <div className={`p-5 ${className}`}>{children}</div>;
}

export function SectionLabel({ children, className = "" }) {
  return (
    <div
      className={[
        "text-[11px] font-semibold uppercase tracking-[0.14em] text-ink-500",
        className,
      ].join(" ")}
    >
      {children}
    </div>
  );
}
