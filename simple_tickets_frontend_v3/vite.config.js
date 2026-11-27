import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv } from 'vite';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { isAppearanceConfigPath } from './src/features/appearance/config.js';

function serveAppearanceConfig(server, directory) {
  server.middlewares.use(async (request, response, next) => {
    const path = request.url?.split('?', 1)[0];
    if (path !== '/config' && !path?.startsWith('/config/')) return next();

    response.setHeader('Cache-Control', 'no-store');
    if (!isAppearanceConfigPath(path)) {
      response.statusCode = 404;
      return response.end();
    }
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      response.statusCode = 405;
      response.setHeader('Allow', 'GET, HEAD');
      return response.end();
    }
    try {
      const body = await readFile(resolve(directory, `.${path}`));
      response.setHeader('Content-Type', 'application/json; charset=utf-8');
      response.setHeader('Content-Length', body.length);
      return response.end(request.method === 'HEAD' ? undefined : body);
    } catch (error) {
      response.statusCode = error?.code === 'ENOENT' || error?.code === 'ENOTDIR' ? 404 : 500;
      return response.end();
    }
  });
}

const appearanceConfig = {
  name: 'appearance-config',
  configureServer(server) { serveAppearanceConfig(server, server.config.publicDir); },
  configurePreviewServer(server) { serveAppearanceConfig(server, resolve(server.config.root, server.config.build.outDir)); },
};

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'BACKEND_');
  const target = process.env.BACKEND_BASE_URL || env.BACKEND_BASE_URL || 'http://127.0.0.1:8000';
  const proxy = {
    '^/api(?:/|$)': {
      target,
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api(?=\/|$)/, ''),
    },
  };

  return {
    plugins: [react(), appearanceConfig],
    server: { host: '127.0.0.1', port: 5173, strictPort: true, proxy },
    preview: { host: '127.0.0.1', port: 5174, strictPort: true, proxy },
  };
});
