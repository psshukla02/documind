import { forwardRef } from "react";

const base =
  "w-full bg-white border border-ink-100 rounded-xl " +
  "px-4 py-2.5 text-sm text-ink-900 placeholder:text-ink-400 " +
  "transition-all ring-focus shadow-soft";

export const Input = forwardRef(function Input(props, ref) {
  const { className = "", ...rest } = props;
  return <input ref={ref} className={`${base} ${className}`} {...rest} />;
});

export const Textarea = forwardRef(function Textarea(props, ref) {
  const { className = "", ...rest } = props;
  return (
    <textarea
      ref={ref}
      className={`${base} font-mono leading-relaxed resize-y ${className}`}
      {...rest}
    />
  );
});

export const Select = forwardRef(function Select(props, ref) {
  const { className = "", children, ...rest } = props;
  return (
    <select
      ref={ref}
      className={`${base} pr-8 bg-no-repeat bg-[length:16px] bg-[right_12px_center] ${className}`}
      style={{
        backgroundImage:
          "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%236e6e73' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><polyline points='6 9 12 15 18 9'/></svg>\")",
        appearance: "none",
      }}
      {...rest}
    >
      {children}
    </select>
  );
});
