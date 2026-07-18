import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev (décision 7) : Vite:5173 sert le front et proxifie /api/* → FastAPI:8000.
// Prod/démo : `vite build` → dist/, servi par FastAPI en StaticFiles (même origine,
// pas de proxy). Le front appelle toujours /api/ask en relatif → identique aux deux modes.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
  },
});
