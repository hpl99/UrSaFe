/**
 * UrSafe Central Coordination & Web Console Server
 * Serves the tactical dashboard and provides REST/Sync endpoints backed by durable SQLite.
 */
const http = require('http');
const fs = require('fs');
const path = require('path');

// Auto-load root .env if present
const envPath = path.join(__dirname, '../../.env');
if (fs.existsSync(envPath)) {
  try {
    const lines = fs.readFileSync(envPath, 'utf8').split('\n');
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
        const idx = trimmed.indexOf('=');
        const k = trimmed.slice(0, idx).trim();
        const v = trimmed.slice(idx + 1).trim();
        if (!process.env[k]) process.env[k] = v;
      }
    }
  } catch (_) {}
}

const { handleApiRequest, attachWebSocket } = require('../api/server');

const PORT = process.env.PORT || 3000;
const PUBLIC_DIR = __dirname;

const mimeTypes = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
};

const server = http.createServer((req, res) => {
  const parsedUrl = new URL(req.url, `http://${req.headers.host || 'localhost:' + PORT}`);
  const pathname = parsedUrl.pathname;

  // API requests: Proxy to standalone backend on port 4000 if active, otherwise handle locally
  if (pathname.startsWith('/api/')) {
    const backendPort = process.env.BACKEND_PORT || 4000;
    const proxyReq = http.request({
      hostname: '127.0.0.1',
      port: backendPort,
      path: req.url,
      method: req.method,
      headers: { ...req.headers, host: `127.0.0.1:${backendPort}` }
    }, (proxyRes) => {
      res.writeHead(proxyRes.statusCode, proxyRes.headers);
      proxyRes.pipe(res);
    });
    proxyReq.on('error', () => {
      // If standalone backend on port 4000 is not running, handle internally
      handleApiRequest(req, res);
    });
    req.pipe(proxyReq);
    return;
  }

  // Static File Serving for Web Console
  let filePath = path.join(PUBLIC_DIR, pathname === '/' ? 'index.html' : pathname);
  const ext = path.extname(filePath).toLowerCase();
  const contentType = mimeTypes[ext] || 'application/octet-stream';

  fs.readFile(filePath, (err, content) => {
    if (err) {
      if (err.code === 'ENOENT') {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('404 Not Found');
      } else {
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        res.end(`Server Error: ${err.code}`);
      }
    } else {
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content);
    }
  });
});

// Attach WebSocket Stream
attachWebSocket(server);

if (require.main === module) {
  server.listen(PORT, () => {
    console.log(`[UrSafe Coordination Hub] Running at http://localhost:${PORT}`);
    console.log(`[Offline Mode] Web console active with zero cloud dependencies.`);
  });
}

module.exports = { server };
