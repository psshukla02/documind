export default function Spinner({ label }) {
  return (
    <div className="flex items-center gap-2 text-slate-400 text-sm">
      <div className="w-4 h-4 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" />
      <span>{label || "Loading…"}</span>
    </div>
  );
}
