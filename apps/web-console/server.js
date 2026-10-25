/**
 * UrSafe Central Coordination & Web Console Server
 * Serves the tactical dashboard and provides REST/Sync endpoints.
 */
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 3000;
const PUBLIC_DIR = __dirname;

const mimeTypes = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
};

// In-Memory Replicated State Store
const ServerState = {
  activeEmergencies: [
    { id: 'inc-001', category: 'FLOOD', urgency: 'CRITICAL', people: 4, status: 'ACCEPTED' },
    { id: 'inc-002', category: 'FIRE', urgency: 'CRITICAL', people: 2, status: 'EN_ROUTE' },
    { id: 'inc-003', category: 'COLLAPSE', urgency: 'HIGH', people: 3, status: 'REPORTED' }
  ],
  syncBacklog: 0,
  activeMeshNodes: 4,
  auditEvents: [
    { event_id: 'evt-001', timestamp: Date.now() - 3600000, actor: 'victim_phone_a', action: 'SOS_CREATED', object: 'inc-001' },
    { event_id: 'evt-002', timestamp: Date.now() - 3000000, actor: 'Unit-Alpha', action: 'SOS_ACCEPTED', object: 'inc-001' }
  ]
};

const server = http.createServer((req, res) => {
  const parsedUrl = new URL(req.url, `http://${req.headers.host}`);
  const pathname = parsedUrl.pathname;

  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // REST API Routes
  if (pathname === '/api/v1/health' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'ok',
      service: 'UrSafe Central Coordination Hub',
      timestamp: Date.now(),
      active_mesh_nodes: ServerState.activeMeshNodes,
      sync_backlog: ServerState.syncBacklog,
      crdt_convergence: '100%'
    }));
    return;
  }

  if (pathname === '/api/v1/emergencies' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(ServerState.activeEmergencies));
    return;
  }

  if (pathname === '/api/v1/sync/bundles' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const bundle = JSON.parse(body);
        const count = (bundle.envelopes || []).length;
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          bundle_id: bundle.bundle_id || 'bundle-sync-ack',
          accepted_count: count,
          duplicate_count: 0,
          rejected_count: 0,
          status: 'SYNCHRONIZED'
        }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON bundle' }));
      }
    });
    return;
  }

  if (pathname === '/api/v1/audit/flight-recorder' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'CHAIN_INTACT',
      chain_length: ServerState.auditEvents.length,
      events: ServerState.auditEvents
    }));
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

server.listen(PORT, () => {
  console.log(`[UrSafe Coordination Hub] Running at http://localhost:${PORT}`);
  console.log(`[Offline Mode] Web console active with zero cloud dependencies.`);
});

module.exports = server;
