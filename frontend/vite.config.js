import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Le proxy fait apparaître l'API et les images sous la même origine que React :
// les cookies de session et le jeton CSRF fonctionnent sans configuration supplémentaire.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/media": "http://127.0.0.1:8000",
    },
  },
});
