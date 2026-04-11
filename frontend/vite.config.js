import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const django = (env.VITE_DJANGO_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

  return {
    plugins: [react()],
    build: {
      outDir: "../static/spa",
      emptyOutDir: true,
    },
    base: mode === "production" ? "/static/spa/" : "/",
    server: {
      port: 5173,
      proxy: {
        "/api": { target: django, changeOrigin: true },
        "/admin": { target: django, changeOrigin: true },
        "/static": { target: django, changeOrigin: true },
      },
    },
  };
});
