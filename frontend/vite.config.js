import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

/** Default Railway backend (override with frontend/.env → VITE_DJANGO_URL). */
const DEFAULT_DJANGO_URL = "https://web-production-9e2ed.up.railway.app";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const django = (env.VITE_DJANGO_URL || DEFAULT_DJANGO_URL).replace(/\/$/, "");
  const base = mode === "production" ? "/static/spa/" : "/";

  return {
    define: {
      "import.meta.env.VITE_DJANGO_URL": JSON.stringify(django),
    },
    base,
    plugins: [
      react(),
      VitePWA({
        registerType: "autoUpdate",
        includeAssets: ["pwa-192.png", "pwa-512.png"],
        manifest: {
          name: "AlyBank",
          short_name: "AlyBank",
          description: "Banking that feels effortless",
          theme_color: "#2563eb",
          background_color: "#f4f7ff",
          display: "standalone",
          orientation: "any",
          // Relative to this web app’s deployed folder (Django serves SPA from / and /static/spa/…)
          scope: "./",
          start_url: "./",
          icons: [
            {
              src: "pwa-192.png",
              sizes: "192x192",
              type: "image/png",
              purpose: "any",
            },
            {
              src: "pwa-512.png",
              sizes: "512x512",
              type: "image/png",
              purpose: "any",
            },
            {
              src: "pwa-512.png",
              sizes: "512x512",
              type: "image/png",
              purpose: "maskable",
            },
          ],
        },
        workbox: {
          globPatterns: ["**/*.{js,css,html,ico,png,svg,woff2}"],
          navigateFallback: "index.html",
          // Do not hijack API / Django admin / health (paths outside SW scope usually fine; extra safety)
          navigateFallbackDenylist: [/^\/api\//, /^\/admin\//, /^\/healthz/],
        },
      }),
    ],
    build: {
      outDir: "../backend/static/spa",
      emptyOutDir: true,
    },
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
