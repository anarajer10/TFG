import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import svgr from 'vite-plugin-svgr'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), svgr()],
  server: {
    port: 3000,
    proxy: {
      // redirige /analizar y /noticias al backend
      "/analizar": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/noticias": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
