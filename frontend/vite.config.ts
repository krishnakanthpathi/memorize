import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'url';
import path from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: parseInt(process.env.VITE_PORT || process.env.FRONTEND_PORT || '6666', 10),
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:7777',
        changeOrigin: true,
      },
    },
  },
});

