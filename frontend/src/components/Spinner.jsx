export default function Spinner({ label }) {
  return (
    <div className="flex items-center gap-3 text-ink-500 text-sm">
      <div className="w-4 h-4 rounded-full border-2 border-brand-400 border-t-transparent animate-spin" />
      {label && <span>{label}</span>}
    </div>
  );
}

export function Typing() {
  return (
    <div className="typing" aria-label="Assistant is typing">
      <span /><span /><span />
    </div>
  );
}

export function Shimmer({ className = "h-4 w-full" }) {
  return <div className={`shimmer ${className}`} />;
}
