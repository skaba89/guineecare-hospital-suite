import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    proxy: {
      // Proxy les appels API vers le backend FastAPI
      "/api": {
        target: process.env.VITE_API_PROXY_TARGET || "http://127.0.0.1:8000",
        changeOrigin: true,
        // WebSocket support — requis pour /api/v1/realtime/ws (dashboard temps réel v1.3)
        ws: true,
      },
    },
  },
});
