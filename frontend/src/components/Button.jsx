import { motion } from "framer-motion";

const VARIANTS = {
  primary:
    "bg-gradient-to-b from-brand-500 to-brand-600 text-white " +
    "hover:from-brand-400 hover:to-brand-500 shadow-soft",
  ghost:
    "bg-white/60 text-ink-900 border border-ink-100 " +
    "hover:bg-white hover:border-ink-200 backdrop-blur-xs",
  soft:
    "bg-brand-50 text-brand-700 border border-brand-100 " +
    "hover:bg-brand-100",
  danger:
    "bg-gradient-to-b from-rose-500 to-rose-600 text-white " +
    "hover:from-rose-400 hover:to-rose-500 shadow-soft",
};

const SIZES = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2 text-sm",
  lg: "px-5 py-2.5 text-sm",
};

export default function Button({
  children,
  onClick,
  disabled = false,
  variant = "primary",
  size = "md",
  type = "button",
  className = "",
}) {
  return (
    <motion.button
      type={type}
      onClick={onClick}
      disabled={disabled}
      whileHover={disabled ? {} : { scale: 1.02 }}
      whileTap={disabled ? {} : { scale: 0.98 }}
      transition={{ type: "spring", stiffness: 500, damping: 30 }}
      className={[
        "inline-flex items-center justify-center gap-2",
        "rounded-full font-medium tracking-tight ring-focus",
        "transition-colors transition-shadow",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        SIZES[size],
        VARIANTS[variant],
        className,
      ].join(" ")}
    >
      {children}
    </motion.button>
  );
}
