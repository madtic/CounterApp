import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In local development the frontend proxies /api to the backend, so the
// browser sees a single origin. In a container the API URL is baked into the
// bundle at build time via VITE_API_BASE_URL.
export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    allowedHosts: true,
    proxy: {
      "/api": {
        target: process.env.BACKEND_PROXY_TARGET || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: "0.0.0.0",
    port: 8080,
    allowedHosts: true,
  },
});
