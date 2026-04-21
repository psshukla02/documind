import { useState } from "react";

export default function CopyButton({ text, label = "Copy" }) {
  const [copied, setCopied] = useState(false);
  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* ignore */
    }
  };
  return (
    <button
      onClick={onCopy}
      className="text-xs px-2 py-1 rounded border border-ink-800 text-slate-300 hover:bg-ink-800"
    >
      {copied ? "✓ Copied" : label}
    </button>
  );
}
