import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Deployed behind one ingress host (/api -> backend). Locally the dev server
// proxies /api (incl. the WebSocket upgrade) to the backend on :8000.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        ws: true,
      },
    },
  },
});
