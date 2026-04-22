/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#f7f8fa",
        ink: {
          900: "#1d1d1f",
          700: "#3d3d41",
          500: "#6e6e73",
          400: "#86868b",
          300: "#a1a1a6",
          200: "#c7c7cc",
          100: "#e5e5ea",
          50:  "#f2f2f5",
        },
        brand: {
          50:  "#eef4ff",
          100: "#dbe8ff",
          200: "#bfd4ff",
          300: "#a5c0ff",
          400: "#7aa7ff",
          500: "#4a87ff",
          600: "#2d6bf0",
          700: "#1e55cc",
        },
        mint: {
          50:  "#f0fdf4",
          100: "#dcfce7",
          200: "#bbf7d0",
          400: "#86efac",
          500: "#4ade80",
        },
        lavender: {
          50:  "#faf5ff",
          100: "#f3e8ff",
          200: "#e9d5ff",
          400: "#c4b5fd",
          500: "#a78bfa",
        },
        peach: {
          50:  "#fef3e2",
          100: "#fde4b8",
          400: "#fdba74",
        },
      },
      fontFamily: {
        sans: ['"SF Pro Display"', '"SF Pro Text"', "Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ['"SF Mono"', "JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        soft: "0 1px 2px rgba(16,24,40,0.04), 0 2px 8px rgba(16,24,40,0.04)",
        card: "0 1px 2px rgba(16,24,40,0.04), 0 8px 24px -12px rgba(16,24,40,0.10)",
        lift: "0 10px 30px -12px rgba(16,24,40,0.15), 0 4px 10px -4px rgba(16,24,40,0.08)",
        glow: "0 0 0 4px rgba(122,167,255,0.18)",
      },
      backdropBlur: {
        xs: "2px",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: 0, transform: "translateY(6px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
        "shimmer": {
          "0%":   { backgroundPosition: "-400px 0" },
          "100%": { backgroundPosition: "400px 0" },
        },
        "blink": {
          "0%, 80%, 100%": { opacity: 0.2, transform: "translateY(0)" },
          "40%":           { opacity: 1,   transform: "translateY(-2px)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.35s cubic-bezier(0.22,1,0.36,1) both",
        "shimmer": "shimmer 1.6s linear infinite",
      },
    },
  },
  plugins: [],
};
