import { useState } from "react";
import { motion } from "framer-motion";

export default function CopyButton({ text, label = "Copy" }) {
  const [copied, setCopied] = useState(false);
  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1400);
    } catch {
      /* ignore */
    }
  };
  return (
    <motion.button
      onClick={onCopy}
      whileTap={{ scale: 0.96 }}
      className={[
        "text-xs px-2.5 py-1 rounded-full",
        "border border-ink-100 text-ink-700 bg-white/70",
        "hover:bg-white hover:border-ink-200 transition",
      ].join(" ")}
    >
      {copied ? "✓ Copied" : label}
    </motion.button>
  );
}
