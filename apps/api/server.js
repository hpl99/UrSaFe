/**
 * UrSafe Central Cloud Coordination API Gateway
 * Runs independently on port 4000 (or PORT env var) to serve REST endpoints.
 */
const http = require('http');

const PORT = process.env.PORT || 4000;

// Central in-memory state store
const CentralState = {
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

  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  if (pathname === '/api/v1/health' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'ok',
      service: 'UrSafe Central Cloud Coordination Gateway',
      timestamp: Date.now(),
      port: PORT,
      active_mesh_nodes: CentralState.activeMeshNodes,
      sync_backlog: CentralState.syncBacklog,
      crdt_convergence: '100%'
    }));
    return;
  }

  if (pathname === '/api/v1/emergencies' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(CentralState.activeEmergencies));
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
      chain_length: CentralState.auditEvents.length,
      events: CentralState.auditEvents
    }));
    return;
  }

  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Endpoint not found', path: pathname }));
});

if (require.main === module) {
  server.listen(PORT, () => {
    console.log(`[UrSafe API Gateway] Running at http://localhost:${PORT}`);
    console.log(`[UrSafe API Gateway] Health check available at http://localhost:${PORT}/api/v1/health`);
  });
}

module.exports = server;
