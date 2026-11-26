import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'BACKEND_');
  const target = process.env.BACKEND_BASE_URL || env.BACKEND_BASE_URL || 'http://127.0.0.1:18080';
  const proxy = {
    '^/api(?:/|$)': {
      target,
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api(?=\/|$)/, ''),
    },
  };

  return {
    plugins: [react()],
    server: { host: '127.0.0.1', port: 5173, strictPort: true, proxy },
    preview: { host: '127.0.0.1', port: 5174, strictPort: true, proxy },
  };
});
