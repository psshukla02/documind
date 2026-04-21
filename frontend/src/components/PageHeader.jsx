export default function PageHeader({ title, subtitle, actions }) {
  return (
    <div className="px-8 py-5 border-b border-ink-800 flex items-center justify-between bg-ink-900/40">
      <div>
        <h1 className="text-2xl font-semibold text-white">{title}</h1>
        {subtitle && (
          <p className="text-sm text-slate-400 mt-0.5">{subtitle}</p>
        )}
      </div>
      <div className="flex gap-2">{actions}</div>
    </div>
  );
}
