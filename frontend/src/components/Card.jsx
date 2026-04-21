export function Card({ children, className = "" }) {
  return (
    <div className={`bg-ink-900 border border-ink-800 rounded-lg ${className}`}>
      {children}
    </div>
  );
}

export function CardHeader({ children, className = "" }) {
  return (
    <div className={`px-4 py-3 border-b border-ink-800 font-semibold text-slate-200 ${className}`}>
      {children}
    </div>
  );
}

export function CardBody({ children, className = "" }) {
  return <div className={`p-4 ${className}`}>{children}</div>;
}
