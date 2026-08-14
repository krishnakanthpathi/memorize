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
    host: '0.0.0.0',
    port: parseInt(process.env.VITE_PORT || process.env.FRONTEND_PORT || '8888', 10),
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://127.0.0.1:7777',
        changeOrigin: true,
        secure: false,
      },
    },
  },
});



