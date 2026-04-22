import { motion } from "framer-motion";

const VARIANTS = {
  primary:
    "bg-brand-600 text-white hover:bg-brand-700 shadow-lift",
  ghost:
    "bg-white text-ink-900 border border-ink-200 " +
    "hover:border-brand-300 hover:text-brand-700 shadow-soft",
  soft:
    "bg-brand-50 text-brand-700 border border-brand-200 " +
    "hover:bg-brand-100",
  danger:
    "bg-rose-600 text-white hover:bg-rose-700 shadow-lift",
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
