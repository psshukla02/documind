import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In production (GitHub Pages) assets live under /documind/. In dev
// we use the plain root so the Vite proxy can forward /api to localhost.
// VITE_BASE lets us override the subpath (e.g. for a custom domain).
const base = process.env.VITE_BASE || "/documind/";

export default defineConfig(({ command }) => ({
  plugins: [react()],
  base: command === "build" ? base : "/",
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
}));
