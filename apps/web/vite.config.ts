import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({
  plugins: [react()],
  server: {
    port: Number(process.env.WONDER_WEB_PORT || 5173),
    strictPort: true,
    proxy: {
      "/v1": {
        target: `http://127.0.0.1:${process.env.WONDER_API_PORT || 8000}`,
        changeOrigin: true,
      },
    },
  },
});
