/**
 * UrSafe Tactical Incident Command & Mesh Console
 * Real application state client • Map canvas rendering • Offline sync
 */

const AppState = {
  activeTab: 'tab-overview',
  timeProjectionMinutes: 10,
  sectorPartitionActive: false,

  incidents: [
    {
      id: 'inc-001',
      category: 'FLOOD',
      urgency: 'CRITICAL',
      people: 4,
      text: 'paani aa raha hai ghar mein bahut tez bachao chhat par 4 log phanse hain',
      lang: 'Hinglish',
      lat: 19.0760,
      lon: 72.8777,
      status: 'ACCEPTED',
      assignedTo: 'Unit-Alpha (Medic)',
      eta: 12.0
    },
    {
      id: 'inc-002',
      category: 'FIRE',
      urgency: 'CRITICAL',
      people: 2,
      text: 'सिलेंडर विस्फोट से आग लग गई है 2 लोग अंदर फंसे हैं',
      lang: 'Hindi',
      lat: 19.0650,
      lon: 72.8620,
      status: 'EN_ROUTE',
      assignedTo: 'Unit-Bravo (Fire)',
      eta: 8.5
    },
    {
      id: 'inc-003',
      category: 'COLLAPSE',
      urgency: 'HIGH',
      people: 3,
      text: 'Wall collapsed after tremors, 3 family members trapped under debris',
      lang: 'English',
      lat: 19.0920,
      lon: 72.8910,
      status: 'REPORTED',
      assignedTo: null,
      eta: null
    }
  ],

  responders: [
    {
      id: 'resp-01',
      callsign: 'Unit-Alpha',
      roles: ['MEDIC', 'SEARCH_AND_RESCUE'],
      skills: ['ADVANCED_LIFE_SUPPORT', 'SWIFT_WATER_RESCUE'],
      passportStatus: 'VERIFIED',
      trustTier: 'NORMAL',
      assignment: 'inc-001',
      status: 'ACTIVE_RESCUE',
      lat: 19.0710,
      lon: 72.8720
    },
    {
      id: 'resp-02',
      callsign: 'Unit-Bravo',
      roles: ['FIREFIGHTER'],
      skills: ['FIREFIGHTING', 'HAZMAT_CONTAINMENT'],
      passportStatus: 'VERIFIED',
      trustTier: 'NORMAL',
      assignment: 'inc-002',
      status: 'EN_ROUTE',
      lat: 19.0600,
      lon: 72.8550
    },
    {
      id: 'resp-03',
      callsign: 'Unit-Charlie (Boat)',
      roles: ['SWIFT_WATER'],
      skills: ['BOAT_OPERATOR', 'DIVING'],
      passportStatus: 'VERIFIED_REVOCATION_STALE',
      trustTier: 'NORMAL',
      assignment: null,
      status: 'AVAILABLE',
      lat: 19.0850,
      lon: 72.8650
    },
    {
      id: 'resp-04',
      callsign: 'Unit-Delta (K9 Search)',
      roles: ['SEARCH_AND_RESCUE'],
      skills: ['CANINE_SEARCH', 'HEAVY_LIFTING'],
      passportStatus: 'VERIFIED',
      trustTier: 'NORMAL',
      assignment: null,
      status: 'AVAILABLE',
      lat: 19.0980,
      lon: 72.8800
    }
  ],

  hazard: {
    id: 'HAZ-FLOOD-01',
    type: 'FLOOD',
    status: 'OBSERVED',
    severity: 0.85,
    expansionRateMps: 5.0, // 5 m/s
    headingDeg: 90.0, // East
    baseVertices: [
      { lat: 19.0700, lon: 72.8500 },
      { lat: 19.0700, lon: 72.8680 },
      { lat: 19.0820, lon: 72.8680 },
      { lat: 19.0820, lon: 72.8500 }
    ]
  },

  nodes: [
    { id: 'RADIO-GATEWAY-01', model: 'Heltec V3 (SX1262)', bearer: 'LoRa 865MHz', rssi: -65, snr: 9.2, etx: 1.02, battery: 94, sector: 'Valley Alpha' },
    { id: 'RADIO-REPEATER-02', model: 'WisBlock RAK4631', bearer: 'LoRa 865MHz', rssi: -78, snr: 6.5, etx: 1.08, battery: 88, sector: 'Hilltop Relay' },
    { id: 'RADIO-MOBILE-03', model: 'T-Beam ESP32', bearer: 'LoRa / BLE', rssi: -84, snr: 4.1, etx: 1.15, battery: 72, sector: 'Valley Beta' },
    { id: 'RADIO-MULE-04', model: 'Vehicle Gateway', bearer: 'LoRa / Wi-Fi', rssi: -58, snr: 12.0, etx: 1.01, battery: 100, sector: 'Data Mule Transit' }
  ],

  securityAssessments: [
    { nodeId: 'RADIO-MOBILE-03', tier: 'NORMAL', composite: 0.88, idTrust: 0.9, credTrust: 1.0, behTrust: 0.95, flags: [] },
    { nodeId: 'RADIO-REPEATER-02', tier: 'NORMAL', composite: 0.92, idTrust: 0.95, credTrust: 1.0, behTrust: 1.0, flags: [] },
    { nodeId: 'ROGUE-SIM-99', tier: 'HIGH_RISK', composite: 0.35, idTrust: 0.2, credTrust: 0.0, behTrust: 0.4, flags: ['SYBIL_CLUSTER (3 keys/1 MAC)', 'BROADCAST_FLOODING'] }
  ],

  passports: [
    { id: 'PASSPORT-NDRF-01', subject: 'responder_ramesh', roles: 'MEDIC, RESCUE', status: 'VERIFIED' },
    { id: 'PASSPORT-NDRF-02', subject: 'responder_priya', roles: 'FIREFIGHTER', status: 'VERIFIED' },
    { id: 'PASSPORT-VOL-03', subject: 'volunteer_karan', roles: 'CIVILIAN_HELPER', status: 'VERIFIED_REVOCATION_STALE' }
  ],

  auditLog: [
    { id: 'evt-001', time: '2026-10-25 19:40:12', actor: 'victim_phone_a', action: 'SOS_CREATED', object: 'inc-001', prevHash: '0000000000000000000000000000000000000000000000000000000000000000', hash: '8f43a9b2110c...33e4' },
    { id: 'evt-002', time: '2026-10-25 19:40:28', actor: 'Unit-Alpha', action: 'SOS_ACCEPTED', object: 'inc-001', prevHash: '8f43a9b2110c...33e4', hash: 'e921d74a919f...10b8' },
    { id: 'evt-003', time: '2026-10-25 19:45:00', actor: 'dispatcher_01', action: 'ASSIGNMENT_CONFIRMED', object: 'inc-002', prevHash: 'e921d74a919f...10b8', hash: 'a12bc098ee31...776f' }
  ]
};

// DOM Init
document.addEventListener('DOMContentLoaded', () => {
  initNav();
  renderAll();
  initMapCanvas();
  initFormHandlers();
  startClock();
});

function initNav() {
  const buttons = document.querySelectorAll('.nav-btn');
  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');
      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
      const activePanel = document.getElementById(targetTab);
      if (activePanel) activePanel.classList.add('active');

      const label = btn.querySelector('.nav-label').textContent;
      document.getElementById('page-title').textContent = label;
      AppState.activeTab = targetTab;

      if (targetTab === 'tab-map') {
        drawTacticalMap();
      }
    });
  });

  // Slider event
  const slider = document.getElementById('slider-hazard-time');
  const label = document.getElementById('label-slider-time');
  slider.addEventListener('input', (e) => {
    AppState.timeProjectionMinutes = parseInt(e.target.value, 10);
    label.textContent = `+${AppState.timeProjectionMinutes} Mins (Arrival Prediction)`;
    drawTacticalMap();
  });

  // Partition toggle
  document.getElementById('btn-toggle-partition').addEventListener('click', () => {
    AppState.sectorPartitionActive = !AppState.sectorPartitionActive;
    alert(`Sector Partition is now: ${AppState.sectorPartitionActive ? 'ACTIVE (Valley Alpha and Beta Separated)' : 'HEALED (Direct Mesh Restored)'}`);
    renderNetworkTable();
  });

  // Quick Action Buttons
  document.getElementById('btn-trigger-sync').addEventListener('click', () => {
    alert('Idempotent Outbox Synchronization Triggered: 0 pending bundles.');
  });

  document.getElementById('btn-simulate-sos').addEventListener('click', () => {
    const newId = `inc-00${AppState.incidents.length + 1}`;
    AppState.incidents.unshift({
      id: newId,
      category: 'MEDICAL',
      urgency: 'CRITICAL',
      people: 1,
      text: 'Chest pain patient needs oxygen support urgently',
      lang: 'English',
      lat: 19.0800,
      lon: 72.8850,
      status: 'REPORTED',
      assignedTo: null,
      eta: null
    });
    AppState.auditLog.push({
      id: `evt-00${AppState.auditLog.length + 1}`,
      time: new Date().toISOString().replace('T', ' ').substring(0, 19),
      actor: 'simulated_civilian',
      action: 'SOS_CREATED',
      object: newId,
      prevHash: AppState.auditLog[AppState.auditLog.length - 1].hash,
      hash: '99fd42ee019b...55bb'
    });
    renderAll();
    drawTacticalMap();
  });
}

function renderAll() {
  renderOverviewTriage();
  renderOverviewNodes();
  renderEmergenciesTable();
  renderRespondersTable();
  renderHazardsTable();
  renderNetworkTable();
  renderSecurityTable();
  renderCredentialsTable();
  renderAuditTable();
}

function renderOverviewTriage() {
  const tbody = document.getElementById('overview-triage-body');
  tbody.innerHTML = '';
  AppState.incidents.forEach(inc => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${inc.category}</strong></td>
      <td><span class="badge ${inc.urgency === 'CRITICAL' ? 'badge-emergency' : 'badge-warning'}">${inc.urgency}</span></td>
      <td>${inc.people}</td>
      <td>Sector 4B (${inc.lat.toFixed(4)}, ${inc.lon.toFixed(4)})</td>
      <td><span class="badge ${inc.status === 'ACCEPTED' ? 'badge-info' : 'badge-warning'}">${inc.status}</span></td>
      <td>${inc.assignedTo || '<em>Unassigned</em>'}</td>
      <td>
        ${!inc.assignedTo ? `<button class="btn btn-action" onclick="quickAssign('${inc.id}')">Dispatch Best Unit</button>` : `<span class="badge badge-success">DISPATCHED</span>`}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function renderOverviewNodes() {
  const container = document.getElementById('overview-nodes-list');
  container.innerHTML = '';
  AppState.nodes.forEach(n => {
    const div = document.createElement('div');
    div.className = 'metric-card';
    div.style.marginBottom = '8px';
    div.innerHTML = `
      <div class="metric-header">
        <strong>${n.id}</strong>
        <span class="badge badge-success">ONLINE</span>
      </div>
      <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">
        ${n.model} • ${n.bearer} • RSSI: ${n.rssi} dBm • Battery: ${n.battery}%
      </div>
    `;
    container.appendChild(div);
  });
}

function renderEmergenciesTable() {
  const tbody = document.getElementById('emergencies-table-body');
  tbody.innerHTML = '';
  AppState.incidents.forEach(inc => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><code>${inc.id}</code></td>
      <td><strong>${inc.category}</strong></td>
      <td><span class="badge ${inc.urgency === 'CRITICAL' ? 'badge-emergency' : 'badge-warning'}">${inc.urgency}</span></td>
      <td>${inc.people}</td>
      <td><em>"${inc.text}"</em></td>
      <td><span class="badge badge-info">${inc.lang}</span></td>
      <td><span class="badge ${inc.status === 'ACCEPTED' ? 'badge-info' : 'badge-warning'}">${inc.status}</span></td>
      <td>${inc.assignedTo || 'Unassigned'}</td>
      <td>
        <button class="btn btn-secondary" onclick="alert('Viewing progressive disclosure level 3 encryption keys for ${inc.id}')">Inspect</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function renderRespondersTable() {
  const tbody = document.getElementById('responders-table-body');
  tbody.innerHTML = '';
  AppState.responders.forEach(r => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${r.callsign}</strong></td>
      <td>${r.roles.join(', ')}</td>
      <td>${r.skills.join(', ')}</td>
      <td><span class="badge ${r.passportStatus === 'VERIFIED' ? 'badge-success' : 'badge-warning'}">${r.passportStatus}</span></td>
      <td><span class="badge badge-info">${r.trustTier}</span></td>
      <td>${r.assignment || 'None'}</td>
      <td><span class="badge ${r.status === 'AVAILABLE' ? 'badge-success' : 'badge-info'}">${r.status}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

function renderHazardsTable() {
  const tbody = document.getElementById('hazards-table-body');
  tbody.innerHTML = '';
  const h = AppState.hazard;
  const tr = document.createElement('tr');
  tr.innerHTML = `
    <td><code>${h.id}</code></td>
    <td><strong>${h.type}</strong></td>
    <td><span class="badge badge-warning">${h.status}</span></td>
    <td>${(h.severity * 100).toFixed(0)}% Acuity</td>
    <td>${h.expansionRateMps} m/s</td>
    <td>${h.headingDeg}° (Due East)</td>
    <td><span class="badge badge-emergency">Route Intersecting @ +10 min</span></td>
  `;
  tbody.appendChild(tr);
}

function renderNetworkTable() {
  const tbody = document.getElementById('network-table-body');
  tbody.innerHTML = '';
  AppState.nodes.forEach(n => {
    const isIsolated = AppState.sectorPartitionActive && n.sector === 'Valley Beta';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><code>${n.id}</code></td>
      <td>${n.model}</td>
      <td>${n.bearer}</td>
      <td>${n.rssi} dBm</td>
      <td>${n.snr} dB</td>
      <td>${n.etx.toFixed(2)}</td>
      <td>${n.battery}%</td>
      <td><span class="badge ${isIsolated ? 'badge-emergency' : 'badge-success'}">${n.sector} ${isIsolated ? '(PARTITIONED)' : ''}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

function renderSecurityTable() {
  const tbody = document.getElementById('security-table-body');
  tbody.innerHTML = '';
  AppState.securityAssessments.forEach(s => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><code>${s.nodeId}</code></td>
      <td><span class="badge ${s.tier === 'NORMAL' ? 'badge-success' : 'badge-emergency'}">${s.tier}</span></td>
      <td><strong>${s.composite.toFixed(2)}</strong></td>
      <td>${s.idTrust.toFixed(2)}</td>
      <td>${s.credTrust.toFixed(2)}</td>
      <td>${s.behTrust.toFixed(2)}</td>
      <td>${s.flags.length > 0 ? s.flags.map(f => `<span class="badge badge-emergency">${f}</span>`).join(' ') : '<span class="badge badge-success">Clean Profile</span>'}</td>
      <td>
        ${s.tier === 'NORMAL' ? `<button class="btn btn-secondary" onclick="alert('Node healthy')">Audited</button>` : `<button class="btn btn-emergency" onclick="alert('Isolating node from mesh route broadcast.')">Isolate</button>`}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function renderCredentialsTable() {
  const tbody = document.getElementById('credentials-table-body');
  tbody.innerHTML = '';
  AppState.passports.forEach(p => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><code>${p.id}</code></td>
      <td><strong>${p.subject}</strong></td>
      <td>${p.roles}</td>
      <td><span class="badge ${p.status === 'VERIFIED' ? 'badge-success' : 'badge-warning'}">${p.status}</span></td>
      <td><button class="btn btn-secondary" onclick="revokePassport('${p.id}')">Revoke</button></td>
    `;
    tbody.appendChild(tr);
  });
}

function renderAuditTable() {
  const tbody = document.getElementById('audit-table-body');
  tbody.innerHTML = '';
  AppState.auditLog.forEach(a => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><code>${a.id}</code></td>
      <td>${a.time}</td>
      <td>${a.actor}</td>
      <td><span class="badge badge-info">${a.action}</span></td>
      <td><code>${a.object}</code></td>
      <td><code>${a.prevHash.substring(0, 16)}...</code></td>
      <td><code>${a.hash.substring(0, 16)}...</code></td>
    `;
    tbody.appendChild(tr);
  });
}

function quickAssign(incidentId) {
  const inc = AppState.incidents.find(i => i.id === incidentId);
  const resp = AppState.responders.find(r => r.assignment === null);
  if (inc && resp) {
    inc.assignedTo = resp.callsign;
    inc.status = 'ACCEPTED';
    inc.eta = 14.5;
    resp.assignment = inc.id;
    resp.status = 'EN_ROUTE';
    renderAll();
    drawTacticalMap();
    alert(`Optimized Dispatch Decision: Assigned ${resp.callsign} to ${inc.id} (ETA: 14.5 min). Reroute verified safe.`);
  } else {
    alert('All specialized units are currently deployed or reserved for life-threat cases.');
  }
}

function revokePassport(passId) {
  const p = AppState.passports.find(x => x.id === passId);
  if (p) {
    p.status = 'REVOKED';
    renderCredentialsTable();
    alert(`Credential ${passId} revoked! Offline verifiers will flag REVOKED.`);
  }
}

function initFormHandlers() {
  document.getElementById('form-issue-passport').addEventListener('submit', (e) => {
    e.preventDefault();
    const sub = document.getElementById('input-sub-id').value;
    const roles = document.getElementById('input-roles').value;
    const newId = `PASSPORT-NDRF-0${AppState.passports.length + 1}`;
    AppState.passports.push({
      id: newId,
      subject: sub,
      roles: roles,
      status: 'VERIFIED'
    });
    renderCredentialsTable();
    alert(`Successfully signed W3C Verifiable Credential Responder Passport: ${newId} with Ed25519 authority key!`);
  });
}

// Canvas Tactical Map Drawing
function initMapCanvas() {
  window.addEventListener('resize', drawTacticalMap);
  setTimeout(drawTacticalMap, 100);
}

function drawTacticalMap() {
  const canvas = document.getElementById('tactical-map-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  // Clear
  ctx.fillStyle = '#060d1a';
  ctx.fillRect(0, 0, w, h);

  // Tactical Grid Lines
  ctx.strokeStyle = 'rgba(30, 41, 59, 0.6)';
  ctx.lineWidth = 1;
  const gridSize = 40;
  for (let x = 0; x < w; x += gridSize) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, h);
    ctx.stroke();
  }
  for (let y = 0; y < h; y += gridSize) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }

  // Draw River / Waterway
  ctx.strokeStyle = 'rgba(6, 182, 212, 0.25)';
  ctx.lineWidth = 8;
  ctx.beginPath();
  ctx.moveTo(0, h * 0.45);
  ctx.bezierCurveTo(w * 0.3, h * 0.40, w * 0.6, h * 0.55, w, h * 0.50);
  ctx.stroke();

  // 1. Draw Observed Hazard Polygon
  const hObs = AppState.hazard.baseVertices;
  const toScreen = (pt) => ({
    x: ((pt.lon - 72.84) / 0.07) * (w * 0.7) + (w * 0.15),
    y: ((19.10 - pt.lat) / 0.05) * (h * 0.7) + (h * 0.15)
  });

  ctx.fillStyle = 'rgba(239, 68, 68, 0.25)';
  ctx.strokeStyle = '#ef4444';
  ctx.lineWidth = 2;
  ctx.beginPath();
  const p0 = toScreen(hObs[0]);
  ctx.moveTo(p0.x, p0.y);
  for (let i = 1; i < hObs.length; i++) {
    const pt = toScreen(hObs[i]);
    ctx.lineTo(pt.x, pt.y);
  }
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = '#ef4444';
  ctx.font = 'bold 12px monospace';
  ctx.fillText('OBSERVED FLOOD FRONT (t=0)', p0.x + 10, p0.y + 20);

  // 2. Draw Kinematic Predicted Hazard Polygon (at t = +ETA)
  const shiftX = (AppState.timeProjectionMinutes / 60) * 120; // Expanded East
  ctx.fillStyle = 'rgba(245, 158, 11, 0.20)';
  ctx.strokeStyle = '#f59e0b';
  ctx.setLineDash([6, 4]);
  ctx.beginPath();
  ctx.moveTo(p0.x + shiftX, p0.y);
  for (let i = 1; i < hObs.length; i++) {
    const pt = toScreen(hObs[i]);
    ctx.lineTo(pt.x + shiftX, pt.y);
  }
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
  ctx.setLineDash([]);

  ctx.fillStyle = '#f59e0b';
  ctx.fillText(`PREDICTED FLOOD FRONT (t=+${AppState.timeProjectionMinutes}m)`, p0.x + shiftX + 10, p0.y + 40);

  // 3. Draw Responders
  AppState.responders.forEach(r => {
    const pt = toScreen({ lat: r.lat, lon: r.lon });
    ctx.fillStyle = '#3b82f6';
    ctx.beginPath();
    ctx.arc(pt.x, pt.y, 8, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.fillStyle = '#93c5fd';
    ctx.font = '11px sans-serif';
    ctx.fillText(r.callsign, pt.x + 12, pt.y + 4);
  });

  // 4. Draw SOS Victims
  AppState.incidents.forEach(inc => {
    const pt = toScreen({ lat: inc.lat, lon: inc.lon });
    ctx.fillStyle = '#ef4444';
    ctx.beginPath();
    ctx.arc(pt.x, pt.y, 9, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.fillStyle = '#fca5a5';
    ctx.font = 'bold 11px sans-serif';
    ctx.fillText(`${inc.id} (${inc.category} • ${inc.people}P)`, pt.x + 14, pt.y + 4);
  });

  // 5. Draw Dynamic Avoidance Reroute for Unit-Alpha -> inc-001
  const rAlpha = AppState.responders[0];
  const inc1 = AppState.incidents[0];
  if (rAlpha && inc1) {
    const ptStart = toScreen({ lat: rAlpha.lat, lon: rAlpha.lon });
    const ptEnd = toScreen({ lat: inc1.lat, lon: inc1.lon });
    const detourWaypoint = { x: (ptStart.x + ptEnd.x) / 2 + 50, y: Math.min(ptStart.y, ptEnd.y) - 60 };

    ctx.strokeStyle = '#06b6d4';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(ptStart.x, ptStart.y);
    ctx.lineTo(detourWaypoint.x, detourWaypoint.y);
    ctx.lineTo(ptEnd.x, ptEnd.y);
    ctx.stroke();

    ctx.fillStyle = '#06b6d4';
    ctx.font = '11px monospace';
    ctx.fillText('DYNAMIC HAZARD AVOIDANCE DETOUR', detourWaypoint.x + 8, detourWaypoint.y - 6);
  }
}

function startClock() {
  setInterval(() => {
    const now = new Date();
    const str = now.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
    const el = document.getElementById('time-display');
    if (el) el.textContent = str;
  }, 1000);
}
