export default function Button({
  children,
  onClick,
  disabled,
  variant = "primary",
  type = "button",
  className = "",
}) {
  const base =
    "inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition disabled:opacity-50 disabled:cursor-not-allowed";
  const styles = {
    primary: "bg-brand-600 hover:bg-brand-500 text-white",
    ghost: "bg-transparent hover:bg-ink-800 text-slate-200 border border-ink-800",
    danger: "bg-red-600 hover:bg-red-500 text-white",
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${styles[variant]} ${className}`}
    >
      {children}
    </button>
  );
}
