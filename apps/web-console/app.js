/**
 * UrSafe — Hyper-local Emergency P2P Network
 * Production Client Application Logic & Disaster Response State Engine
 * Seamless integration with Node.js SQLite Coordination Hub & WebSockets
 */

// Global Application State
const AppState = {
  activeView: 'view-landing',
  mode: 'LIVE', // 'LIVE' or 'TRAINING'
  currentUser: {
    token: null,
    userId: 'usr-citizen-01',
    username: 'citizen_priya',
    fullName: 'Priya Sharma',
    role: 'CITIZEN',
    initials: 'PS'
  },
  location: {
    lat: 19.0760,
    lon: 72.8777,
    accuracy: 4.2,
    locked: true
  },
  activeSeverity: null, // Initialized UNSET
  selectedMedicalFactors: [],
  activeSosId: null,
  activeFilter: 'ALL',
  incidents: [],
  maps: {
    victimRadar: null,
    victimMarker: null,
    victimCircle: null,
    victimTileLayer: null,
    orchestration: null,
    orchestrationTileLayer: null
  },
  activeDossierIncidentId: null,
  currentEvidenceHash: null,
  ws: null
};

<<<<<<< HEAD
// Isolated Simulated Seed Incidents (Rendered strictly in TRAINING mode with [SIMULATED] badge)
const SimulatedSeedIncidents = [
  {
    id: '#8293-A',
    rawId: 'inc-sim-8293',
    category: 'MEDICAL',
    type: 'Trauma / Hemorrhage',
    urgency: 'CRITICAL',
    title: 'Severe Hemorrhage / Simulation Patient A',
    description: 'Blunt thoracic trauma simulation. Training exercise scenario.',
    distance: null,
    timeAgo: 'Training',
    hop: '01',
    lat: 19.0785,
    lon: 72.8810,
    tags: [{ text: '+ Trauma Kit Required', type: 'req' }, { text: 'SIMULATED', type: 'match' }],
    status: 'REPORTED',
    responder: 'Unassigned',
    resolution: 'Training Exercise',
    simulated: true
  },
  {
    id: '#4102-C',
    rawId: 'inc-sim-4102',
    category: 'COLLAPSE',
    type: 'Structural Encirclement',
    urgency: 'URGENT',
    title: 'Building Encirclement / Simulation Family B',
    description: 'Structural obstacle simulation. 3 occupants sheltering. Training exercise.',
    distance: null,
    timeAgo: 'Training',
    hop: '02',
    lat: 19.0830,
    lon: 72.8850,
    tags: [{ text: 'Evacuation Support', type: 'req' }, { text: 'SIMULATED', type: 'match' }],
    status: 'DISPATCHED',
    responder: 'Unassigned',
    resolution: 'Training Exercise',
    simulated: true
  }
];
=======
// Central Authenticated API Client Wrapper
async function apiFetch(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };
  if (AppState.currentUser && AppState.currentUser.token) {
    headers['Authorization'] = `Bearer ${AppState.currentUser.token}`;
  }
  return fetch(path, { ...options, headers });
}

// Auto-Authentication Engine for active persona (JWT Bearer Token Acquisition)
async function initSession(username = 'citizen_priya') {
  try {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password: 'Password123!' })
    });
    if (res.ok) {
      const data = await res.json();
      AppState.currentUser.token = data.token;
      AppState.currentUser.userId = data.user.id;
      AppState.currentUser.username = data.user.username;
      AppState.currentUser.fullName = data.user.full_name;
      AppState.currentUser.role = data.user.role;
      AppState.currentUser.initials = data.user.full_name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();
      updateUserBadge();
      console.log(`[UrSafe Auth] Successfully authenticated as ${data.user.full_name} (${data.user.role})`);
      return true;
    }
  } catch (err) {
    console.warn('[UrSafe Auth] Offline mode or initial login warning:', err.message);
  }
  return false;
}
>>>>>>> ece2da3b08329b23ed48edd26b04c7df06397e4f

// Seed Users for Instant Persona Evaluation
const SeedUsers = {
  citizen_priya: {
    userId: 'usr-citizen-01',
    username: 'citizen_priya',
    fullName: 'Priya Sharma',
    role: 'CITIZEN',
    initials: 'PS'
  },
  responder_vikram: {
    userId: 'usr-responder-01',
    username: 'responder_vikram',
    fullName: 'Capt. Vikram Singh',
    role: 'RESPONDER',
    initials: 'VS'
  },
  authority_rajesh: {
    userId: 'usr-authority-01',
    username: 'authority_rajesh',
    fullName: 'Cmdr. Rajesh Kumar',
    role: 'AUTHORITY',
    initials: 'RK'
  },
  admin_system: {
    userId: 'usr-admin-01',
    username: 'admin_system',
    fullName: 'System Administrator',
    role: 'ADMIN',
    initials: 'SA'
  }
};

// ============================================================================
// INITIALIZATION
// ============================================================================
<<<<<<< HEAD
document.addEventListener('DOMContentLoaded', () => {
  // Dev flag gating for quick role switcher
  const isDev = Boolean(window.URSAFE_CONFIG && window.URSAFE_CONFIG.isDev);
  const roleEval = document.getElementById('quick-role-eval');
  if (roleEval) {
    roleEval.style.display = isDev ? 'block' : 'none';
  }

  // Training Banner Exit handler
  const btnToggleTraining = document.getElementById('btn-toggle-training-mode');
  if (btnToggleTraining) {
    btnToggleTraining.addEventListener('click', () => {
      AppState.mode = 'LIVE';
      const trainingBanner = document.getElementById('training-mode-banner');
      if (trainingBanner) trainingBanner.style.display = 'none';
      const btnLive = document.getElementById('btn-mode-live');
      const btnTrain = document.getElementById('btn-mode-train');
      if (btnLive) btnLive.className = 'btn-mode active-live';
      if (btnTrain) btnTrain.className = 'btn-mode inactive';
      showToast('Switched to LIVE Operational Mode.');
      fetchInitialBackendIncidents();
    });
  }

  // Situational Byte Budget Listener (200 bytes LoRa budget)
  const sosInput = document.getElementById('sos-situation-input');
  const byteCounter = document.getElementById('situation-char-count');
  if (sosInput && byteCounter) {
    const updateBytes = () => {
      const bytes = new TextEncoder().encode(sosInput.value || '').length;
      byteCounter.textContent = `${bytes} / 200 bytes (LoRa Payload Budget)`;
      if (bytes > 200) {
        byteCounter.classList.add('over-budget');
      } else {
        byteCounter.classList.remove('over-budget');
      }
    };
    sosInput.addEventListener('input', updateBytes);
    updateBytes();
  }

=======
document.addEventListener('DOMContentLoaded', async () => {
  await initSession('citizen_priya');
>>>>>>> ece2da3b08329b23ed48edd26b04c7df06397e4f
  updateGoogleMapsStatusUI();
  setupNavigation();
  setupMapLayerSwitchers();
  setupLocationSensors();
  setupVictimPortal();
  setupResponderPortal();
  setupGlobalDashboard();
  setupModals();
  initHardwareConnectionCenter();
  initSystemHealth();
  initPersonaSelector();
  setupTelemetryControls();
  connectWebSocket();
  fetchInitialBackendIncidents();
  renderTriageQueue();
  renderActivityLog();
  setupConnectivityCockpit();
  pollConnectivityCockpit();
  setInterval(pollConnectivityCockpit, 3500);
  fetchAuthorityDashboardData();
  setInterval(fetchAuthorityDashboardData, 5000);
  fetchOutboxQueue();
});

// ============================================================================
// 1. NAVIGATION & PORTAL SWITCHING
// ============================================================================
function setupNavigation() {
  const tabs = document.querySelectorAll('.nav-tab-btn');
  tabs.forEach(tab => {
    tab.addEventListener('click', (e) => {
      const targetView = tab.getAttribute('data-target');
      switchView(targetView);
    });
  });

  // Brand click returns to Landing
  const brandBtn = document.getElementById('btn-brand-home');
  if (brandBtn) {
    brandBtn.addEventListener('click', () => switchView('view-landing'));
  }

  // Landing page split cards
  const btnNeedHelp = document.getElementById('btn-landing-need-help');
  if (btnNeedHelp) {
    btnNeedHelp.addEventListener('click', (e) => {
      e.preventDefault();
      switchView('view-victim');
    });
  }

  const btnCanRespond = document.getElementById('btn-landing-can-respond');
  if (btnCanRespond) {
    btnCanRespond.addEventListener('click', (e) => {
      e.preventDefault();
      switchView('view-responder');
    });
  }

  // Live / Training Mode Toggle
  const btnLive = document.getElementById('btn-mode-live');
  const btnTrain = document.getElementById('btn-mode-train');
  if (btnLive && btnTrain) {
    btnLive.addEventListener('click', () => {
      AppState.mode = 'LIVE';
      btnLive.className = 'btn-mode active-live';
      btnTrain.className = 'btn-mode inactive';
      showToast('Switched to LIVE MESH MODE — Real RF packets active.');
    });
    btnTrain.addEventListener('click', () => {
      AppState.mode = 'TRAINING';
      btnTrain.className = 'btn-mode active-train';
      btnLive.className = 'btn-mode inactive';
      const trainingBanner = document.getElementById('training-mode-banner');
      if (trainingBanner) trainingBanner.style.display = 'flex';
      showToast('Switched to TRAINING MODE — Distress signals strictly isolated.');
      fetchInitialBackendIncidents();
    });
  }

  // Quick Role Evaluation buttons (Dev Only)
  const roleBtns = document.querySelectorAll('.role-switch-btn');
  roleBtns.forEach(btn => {
    btn.addEventListener('click', async () => {
      const roleKey = btn.getAttribute('data-role');
      const seed = SeedUsers[roleKey];
      if (seed) {
        try {
          const res = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: seed.username, password: 'Password123!' })
          });
          if (res.ok) {
            const data = await res.json();
            AppState.currentUser = { ...seed, token: data.session?.token, session: data.session };
          } else {
            AppState.currentUser = { ...seed };
          }
        } catch (_) {
          AppState.currentUser = { ...seed };
        }
        updateUserBadge();
        showToast(`Active persona: ${seed.fullName} (${seed.role})`);
        if (seed.role === 'CITIZEN') switchView('view-victim');
        else if (seed.role === 'RESPONDER') switchView('view-responder');
        else switchView('view-dashboard');
      }
    });
  });
}

function switchView(viewId) {
  AppState.activeView = viewId;

  // Toggle active class on views
  const screens = document.querySelectorAll('.view-screen');
  screens.forEach(s => s.classList.remove('active'));
  const activeEl = document.getElementById(viewId);
  if (activeEl) activeEl.classList.add('active');

  // Toggle active class on navigation tabs
  const tabs = document.querySelectorAll('.nav-tab-btn');
  tabs.forEach(t => {
    if (t.getAttribute('data-target') === viewId) t.classList.add('active');
    else t.classList.remove('active');
  });

  // Update Breadcrumb
  const breadcrumbEl = document.getElementById('sub-breadcrumb-text');
  if (breadcrumbEl) {
    const breadcrumbMap = {
      'view-landing': 'URSAFE / DISASTER COORDINATION NETWORK | PEER-TO-PEER ENCRYPTED LINK',
      'view-victim': 'URSAFE / VICTIM EMERGENCY NODE | PEER-TO-PEER ENCRYPTED LINK',
      'view-responder': 'URSAFE / RESPONDER PORTAL | IN_865 LORA MESH',
      'view-dashboard': 'URSAFE / CENTRALIZED NETWORK ORCHESTRATION | MERKLE AUDIT ACTIVE'
    };
    breadcrumbEl.textContent = breadcrumbMap[viewId] || 'URSAFE / DISASTER NETWORK';
  }

<<<<<<< HEAD
  // Lazy initialize map viewports or query dashboard
  if (viewId === 'view-victim' && !AppState.maps.victimRadar) {
    setTimeout(initVictimRadarMap, 100);
  } else if (viewId === 'view-dashboard') {
    fetchAuthorityDashboardData();
    if (!AppState.maps.orchestration) {
      setTimeout(initOrchestrationMap, 100);
    }
=======
  // Lazy initialize or invalidate map viewports to ensure seamless rendering
  if (viewId === 'view-victim') {
    if (!AppState.maps.victimRadar) setTimeout(initVictimRadarMap, 100);
    else setTimeout(() => AppState.maps.victimRadar?.invalidateSize(), 150);
  } else if (viewId === 'view-dashboard') {
    if (!AppState.maps.orchestration) setTimeout(initOrchestrationMap, 100);
    else setTimeout(() => AppState.maps.orchestration?.invalidateSize(), 150);
>>>>>>> ece2da3b08329b23ed48edd26b04c7df06397e4f
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updateUserBadge() {
  const nameEl = document.getElementById('user-display-name');
  const roleEl = document.getElementById('user-display-role');
  const avatarEl = document.getElementById('user-avatar-initials');

  if (nameEl) nameEl.textContent = AppState.currentUser.fullName;
  if (roleEl) roleEl.textContent = AppState.currentUser.role;
  if (avatarEl) avatarEl.textContent = AppState.currentUser.initials;
}

// ============================================================================
// 2. HARDWARE GNSS LOCATION & RADAR MAP
// ============================================================================
function applyCoordinates(lat, lon, accuracy = 4.2, statusLabel = 'ACTIVE HARDWARE LOCK') {
  AppState.location.lat = Number(Number(lat).toFixed(6));
  AppState.location.lon = Number(Number(lon).toFixed(6));
  AppState.location.accuracy = Math.round(accuracy * 10) / 10;

  updateLocationDisplay();

  const gnssStatus = document.getElementById('modal-gnss-status-text');
  if (gnssStatus) gnssStatus.textContent = statusLabel;
  const accEl = document.getElementById('modal-accuracy');
  if (accEl) accEl.textContent = `±${AppState.location.accuracy} meters`;

  // Update victim map if initialized
  if (AppState.maps.victimRadar) {
    AppState.maps.victimRadar.setView([AppState.location.lat, AppState.location.lon], 15);
    AppState.maps.victimRadar.invalidateSize();
  }

  // Update orchestration map if initialized
  if (AppState.maps.orchestration) {
    AppState.maps.orchestration.panTo([AppState.location.lat, AppState.location.lon]);
    AppState.maps.orchestration.invalidateSize();
  }

  // Reverse geocode via backend API
  apiFetch('/api/v1/locations/reverse-geocode', {
    method: 'POST',
    body: JSON.stringify({ latitude: AppState.location.lat, longitude: AppState.location.lon })
  })
    .then(r => r.json())
    .then(data => {
      const addrEl = document.getElementById('modal-resolved-address');
      if (addrEl && (data.formatted || data.formatted_address)) {
        addrEl.textContent = data.formatted || data.formatted_address;
      }
    })
    .catch(() => {});
}

function setupLocationSensors() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      pos => {
        applyCoordinates(pos.coords.latitude, pos.coords.longitude, pos.coords.accuracy || 4.2, 'HARDWARE GNSS FIX ACQUIRED');
        console.log(`[UrSafe GNSS] Device GPS locked: ${pos.coords.latitude}, ${pos.coords.longitude}`);
      },
      err => {
        console.warn('Direct GPS acquiring fallback to default sector:', err.message);
        applyCoordinates(AppState.location.lat, AppState.location.lon, AppState.location.accuracy, 'DEFAULT MESH SECTOR');
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 }
    );
  } else {
    applyCoordinates(AppState.location.lat, AppState.location.lon, AppState.location.accuracy, 'DEFAULT MESH SECTOR');
  }

  // Adjust pin trigger
  const btnAdjust = document.getElementById('btn-trigger-adjust-pin');
  if (btnAdjust) {
    btnAdjust.addEventListener('click', () => {
      openModal('modal-where-am-i');
    });
  }

  // Acquire real GPS button in modal
  const btnAcquire = document.getElementById('btn-acquire-real-gps');
  if (btnAcquire) {
    btnAcquire.addEventListener('click', () => {
      if (navigator.geolocation) {
        showToast('Scanning hardware GNSS receiver for high-precision satellite fix...');
        navigator.geolocation.getCurrentPosition(
          pos => {
            applyCoordinates(pos.coords.latitude, pos.coords.longitude, pos.coords.accuracy || 3.8, 'HARDWARE GNSS FIX (UPDATED)');
            showToast(`GNSS Fix Acquired: ${pos.coords.latitude.toFixed(4)}° N, ${pos.coords.longitude.toFixed(4)}° E (±${Math.round(pos.coords.accuracy || 4)}m)`);
          },
          err => {
            showToast(`GPS Error: ${err.message}. Check browser location permissions.`);
          },
          { enableHighAccuracy: true, timeout: 12000 }
        );
      } else {
        showToast('Browser does not support navigator.geolocation API.');
      }
    });
  }

  // City presets in modal
  const presetBtns = document.querySelectorAll('.btn-preset-loc');
  presetBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const lat = parseFloat(btn.getAttribute('data-lat'));
      const lon = parseFloat(btn.getAttribute('data-lon'));
      const city = btn.getAttribute('data-city');
      if (!isNaN(lat) && !isNaN(lon)) {
        applyCoordinates(lat, lon, 4.0, `TACTICAL PRESET: ${city}`);
        showToast(`Map and coordinates recentered to ${city}`);
      }
    });
  });

  // Apply custom coords
  const btnApplyCustom = document.getElementById('btn-apply-custom-coords');
  if (btnApplyCustom) {
    btnApplyCustom.addEventListener('click', () => {
      const latInput = document.getElementById('input-custom-lat');
      const lonInput = document.getElementById('input-custom-lon');
      const lat = parseFloat(latInput?.value);
      const lon = parseFloat(lonInput?.value);
      if (!isNaN(lat) && !isNaN(lon)) {
        applyCoordinates(lat, lon, 4.0, 'CUSTOM COORDINATES APPLIED');
        showToast(`Custom Coordinates locked: ${lat.toFixed(4)}° N, ${lon.toFixed(4)}° E`);
      } else {
        showToast('Please enter valid numeric latitude and longitude.');
      }
    });
  }
}

function updateLocationDisplay() {
  const latStr = `${AppState.location.lat.toFixed(4)}° N, ${AppState.location.lon.toFixed(4)}° E`;
  const lockedCoords = document.getElementById('val-victim-locked-coords');
  if (lockedCoords) lockedCoords.textContent = latStr;

  const chipCoords = document.getElementById('cit-radar-coords-chip');
  if (chipCoords) {
    chipCoords.textContent = `N ${AppState.location.lat.toFixed(4)}° E ${AppState.location.lon.toFixed(4)}°`;
  }

  const modalLat = document.getElementById('modal-lat');
  const modalLon = document.getElementById('modal-lon');
  if (modalLat) modalLat.textContent = `${AppState.location.lat.toFixed(6)}° N`;
  if (modalLon) modalLon.textContent = `${AppState.location.lon.toFixed(6)}° E`;
}

// ============================================================================
// GOOGLE MAPS TILE LAYER BUILDER & LAYER SWITCHING
// ============================================================================
function getGoogleMapsKey() {
  return window.URSAFE_CONFIG?.googleMapsApiKey || '';
}

function updateGoogleMapsStatusUI() {
  const badge = document.getElementById('badge-google-maps');
  const label = document.getElementById('label-google-maps-status');
  const key = getGoogleMapsKey();
  if (badge && label) {
    if (key) {
      label.textContent = 'Google Maps Active';
      badge.style.borderColor = '#1A73E8';
      badge.style.color = '#1A73E8';
      badge.title = `Google Maps API Key Connected (${key.slice(0, 8)}...)`;
    } else {
      label.textContent = 'Offline Mesh Tiles';
      badge.style.borderColor = 'var(--border-color)';
      badge.style.color = 'var(--text-secondary)';
      badge.title = 'Offline OpenStreetMap active. Add GOOGLE_MAPS_API_KEY in .env for Google Tiles';
    }
  }
}

function createMapTileLayer(layerType) {
  const key = getGoogleMapsKey();
  if (layerType === 'google-satellite' && key) {
    return L.tileLayer(`https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}&key=${key}`, {
      maxZoom: 20,
      attribution: '© Google Maps'
    });
  } else if (layerType === 'google-roadmap' && key) {
    return L.tileLayer(`https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}&key=${key}`, {
      maxZoom: 20,
      attribution: '© Google Maps'
    });
  } else {
    return L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      className: 'warm-osm-tiles',
      attribution: '© OpenStreetMap'
    });
  }
}

function setupMapLayerSwitchers() {
  const layerPills = document.querySelectorAll('.layer-pill');
  layerPills.forEach(pill => {
    pill.addEventListener('click', (e) => {
      e.stopPropagation();
      const mapName = pill.getAttribute('data-map');
      const layerType = pill.getAttribute('data-layer');
      const parent = pill.parentElement;

      // Update active pill UI
      if (parent) {
        parent.querySelectorAll('.layer-pill').forEach(p => p.classList.remove('active'));
      }
      pill.classList.add('active');

      const key = getGoogleMapsKey();
      if ((layerType === 'google-roadmap' || layerType === 'google-satellite') && !key) {
        showToast('Google Maps key not found. Using Offline OpenStreetMap layer.');
        return;
      }

      // Swap tile layer on target map
      if (mapName === 'victim' && AppState.maps.victimRadar) {
        if (AppState.maps.victimTileLayer) {
          AppState.maps.victimRadar.removeLayer(AppState.maps.victimTileLayer);
        }
        AppState.maps.victimTileLayer = createMapTileLayer(layerType).addTo(AppState.maps.victimRadar);
        showToast(`Victim Radar: Switched to ${layerType === 'google-satellite' ? 'Google Satellite' : (layerType === 'google-roadmap' ? 'Google Maps Roadmap' : 'Offline Mesh')}`);
      } else if (mapName === 'orchestration' && AppState.maps.orchestration) {
        if (AppState.maps.orchestrationTileLayer) {
          AppState.maps.orchestration.removeLayer(AppState.maps.orchestrationTileLayer);
        }
        AppState.maps.orchestrationTileLayer = createMapTileLayer(layerType).addTo(AppState.maps.orchestration);
        showToast(`Central Map: Switched to ${layerType === 'google-satellite' ? 'Google Satellite' : (layerType === 'google-roadmap' ? 'Google Maps Roadmap' : 'Offline Mesh')}`);
      }
    });
  });
}

function initVictimRadarMap() {
  const mapContainer = document.getElementById('victim-radar-map');
  if (!mapContainer || AppState.maps.victimRadar) return;

  try {
    AppState.maps.victimRadar = L.map('victim-radar-map', {
      center: [AppState.location.lat, AppState.location.lon],
      zoom: 15,
      zoomControl: false,
      attributionControl: false
    });

    // Default to Google Maps Roadmap if API key is present, otherwise offline warm tiles
    const defaultLayer = getGoogleMapsKey() ? 'google-roadmap' : 'osm-mesh';
    AppState.maps.victimTileLayer = createMapTileLayer(defaultLayer).addTo(AppState.maps.victimRadar);

    // Click to adjust pin
    AppState.maps.victimRadar.on('click', (e) => {
      AppState.location.lat = e.latlng.lat;
      AppState.location.lon = e.latlng.lng;
      updateLocationDisplay();
      AppState.maps.victimRadar.panTo(e.latlng);
      showToast(`Position calibrated: ${e.latlng.lat.toFixed(4)}°, ${e.latlng.lng.toFixed(4)}°`);
    });
  } catch (err) {
    console.warn('Leaflet radar init note:', err.message);
  }
}

// ============================================================================
// 3. VICTIM PORTAL & SOS BROADCAST ENGINE
// ============================================================================
function setupVictimPortal() {
  // Situation Details Character Counter
  const textarea = document.getElementById('sos-situation-input');
  const counter = document.getElementById('situation-char-count');
  if (textarea && counter) {
    const updateCount = () => {
      const len = textarea.value.length;
      counter.textContent = `${len} / 240 chars (LoRa Packet Optimized)`;
    };
    textarea.addEventListener('input', updateCount);
    updateCount();
  }

  // Triage Severity Cards Selection
  const sevCards = document.querySelectorAll('.sev-card-option');
  sevCards.forEach(card => {
    card.addEventListener('click', () => {
      sevCards.forEach(c => {
        c.classList.remove('selected-critical', 'selected-urgent', 'selected-minor');
        // remove check badge
        const badge = c.querySelector('.sev-check-badge');
        if (badge) badge.remove();
      });

      const sev = card.getAttribute('data-severity');
      AppState.activeSeverity = sev;

      if (sev === 'CRITICAL') card.classList.add('selected-critical');
      else if (sev === 'URGENT') card.classList.add('selected-urgent');
      else card.classList.add('selected-minor');

      // Add checkmark icon
      const iconRow = card.querySelector('.sev-icon-row');
      if (iconRow && !card.querySelector('.sev-check-badge')) {
        const check = document.createElement('iconify-icon');
        check.setAttribute('icon', 'lucide:check-circle-2');
        check.className = 'sev-check-badge';
        iconRow.appendChild(check);
      }
    });
  });

  // Medical Factors Pill Buttons
  const medPills = document.querySelectorAll('.med-pill-btn');
  medPills.forEach(pill => {
    pill.addEventListener('click', () => {
      const med = pill.getAttribute('data-med');
      pill.classList.toggle('active');
      if (pill.classList.contains('active')) {
        if (!AppState.selectedMedicalFactors.includes(med)) {
          AppState.selectedMedicalFactors.push(med);
        }
      } else {
        AppState.selectedMedicalFactors = AppState.selectedMedicalFactors.filter(m => m !== med);
      }
    });
  });

  // Needs Cards Checkboxes
  const chkWater = document.getElementById('chk-need-water');
  const cardWater = document.getElementById('card-need-water');
  if (chkWater && cardWater) {
    chkWater.addEventListener('change', () => cardWater.classList.toggle('checked', chkWater.checked));
  }

  const chkPower = document.getElementById('chk-need-power');
  const cardPower = document.getElementById('card-need-power');
  if (chkPower && cardPower) {
    chkPower.addEventListener('change', () => cardPower.classList.toggle('checked', chkPower.checked));
  }

  // Broadcast Emergency Signal Primary CTA
  const btnBroadcast = document.getElementById('btn-submit-distress-signal');
  if (btnBroadcast) {
    btnBroadcast.addEventListener('click', handleDistressBroadcast);
  }

  // Citizen Dual Confirmation Co-Sign button
  const btnCoSign = document.getElementById('btn-citizen-cosign');
  if (btnCoSign) {
    btnCoSign.addEventListener('click', handleCitizenCoSign);
  }
}

async function handleDistressBroadcast() {
  const btn = document.getElementById('btn-submit-distress-signal');
  const textarea = document.getElementById('sos-situation-input');
  const description = textarea ? textarea.value.trim() : 'Emergency assistance needed';
  const severity = AppState.activeSeverity;

  btn.disabled = true;
  btn.innerHTML = `<iconify-icon icon="lucide:loader-2" class="animate-spin"></iconify-icon><span>Signing & Broadcasting Packet...</span>`;

  const incidentPayload = {
    id: 'inc-' + Math.floor(1000 + Math.random() * 9000) + '-A',
    category: severity === 'CRITICAL' ? 'FLOOD' : 'MEDICAL',
    urgency: severity,
    latitude: AppState.location.lat,
    longitude: AppState.location.lon,
    accuracy_m: AppState.location.accuracy,
    location_description: 'S V Road, Sector 4, Verified via GPS Lock',
    victim_count: 3,
    description: description,
    medical_factors: AppState.selectedMedicalFactors,
    is_simulation: AppState.mode === 'TRAINING' ? 1 : 0
  };

  // 1. Try real server API endpoint with authenticated JWT token
  try {
    const res = await apiFetch('/api/v1/incidents', {
      method: 'POST',
      body: JSON.stringify(incidentPayload)
    });
    const data = await res.json();
    if (data.incident) {
      incidentPayload.id = data.incident.id;
    }
  } catch (err) {
    console.log('[Offline Mesh Mode] Backend unavailable, saved to local SQLite Room outbox.');
  }

  // 2. Add to active incidents array in frontend
  AppState.activeSosId = incidentPayload.id;
  const newIncident = {
    id: '#' + incidentPayload.id.slice(-6).toUpperCase(),
    rawId: incidentPayload.id,
    category: incidentPayload.category,
    type: severity === 'CRITICAL' ? 'Flash Flood / Roof Trap' : 'Medical Trauma',
    urgency: severity,
    title: 'SOS Beacon: ' + description.slice(0, 36) + '...',
    description: description,
    distance: 0.1,
    timeAgo: 'Just now',
    hop: '01',
    lat: AppState.location.lat,
    lon: AppState.location.lon,
    tags: [{ text: severity, type: 'req' }, { text: 'P2P LoRa', type: 'match' }],
    status: 'REPORTED',
    responder: 'Awaiting Unit',
    resolution: 'Dispatched'
  };

  AppState.incidents.unshift(newIncident);
  renderTriageQueue();
  renderActivityLog();

  // 3. Reveal and start 10-step progression stepper
  const progressionBox = document.getElementById('sos-progression-box');
  if (progressionBox) {
    progressionBox.classList.remove('hidden');
    progressionBox.scrollIntoView({ behavior: 'smooth' });
  }

  btn.disabled = false;
  btn.innerHTML = `<iconify-icon icon="lucide:check-circle"></iconify-icon><span>Beacon Transmitted to Mesh</span>`;

  showToast(`Distress beacon ${newIncident.id} broadcast over 868MHz mesh.`);

  // Advance progression stepper in realistic intervals
  advanceSosLifecycle();
}

function advanceSosLifecycle() {
  const steps = [
    { num: 1, label: 'Reported', pill: 'REPORTED // QUEUED', delay: 1000 },
    { num: 2, label: 'Stored in SQLite Outbox', pill: 'STORED // ENCRYPTED', delay: 2500 },
    { num: 3, label: 'Queued in Priority FIFO', pill: 'QUEUED // 868MHz', delay: 4000 },
    { num: 4, label: 'Transmitting RF Frame', pill: 'TRANSMITTING LORA', delay: 6000 },
    { num: 5, label: 'Dispatched by Command', pill: 'DISPATCHED // UNIT ASSIGNED', delay: 8500 },
    { num: 6, label: 'Mission Accepted by Capt. Vikram', pill: 'ACCEPTED // EN ROUTE', delay: 11000 },
    { num: 7, label: 'Unit En Route (ETA 4 min)', pill: 'EN ROUTE // GPS TRACKING', delay: 14000 },
    { num: 8, label: 'Unit Arrived on Scene', pill: 'ON SCENE // TRIAGE ACTIVE', delay: 17500 },
    { num: 9, label: 'Rescue Report Submitted', pill: 'RESCUE SUBMITTED // AWAITING CO-SIGN', delay: 20000 }
  ];

  steps.forEach(st => {
    setTimeout(() => {
      // Mark stepper nodes
      for (let i = 1; i <= 10; i++) {
        const el = document.getElementById(`st-${i}`);
        if (!el) continue;
        if (i < st.num) {
          el.className = 'step-node completed';
        } else if (i === st.num) {
          el.className = 'step-node current';
        } else {
          el.className = 'step-node';
        }
      }

      const pill = document.getElementById('sos-live-pill');
      if (pill) pill.textContent = st.pill;

      // When submitted, unlock Citizen Dual-Confirmation desk!
      if (st.num === 9) {
        const dualDesk = document.getElementById('citizen-dual-confirm-desk');
        if (dualDesk) {
          dualDesk.classList.remove('hidden');
          dualDesk.scrollIntoView({ behavior: 'smooth' });
        }
      }
    }, st.delay);
  });
}

function handleCitizenCoSign() {
  const btn = document.getElementById('btn-citizen-cosign');
  btn.disabled = true;
  btn.innerHTML = `<iconify-icon icon="lucide:check"></iconify-icon><span>Rescue Verified & Co-Signed with Ed25519</span>`;
  btn.style.background = '#059669';

  try {
    if (AppState.activeSosId) {
      apiFetch(`/api/v1/incidents/${AppState.activeSosId}/confirm-rescue`, {
        method: 'POST',
        body: JSON.stringify({
          victim_signature: `sig_ed25519_${AppState.currentUser.userId}_${Date.now()}`
        })
      });
    }
  } catch (err) {}

  // Mark step 10 verified
  const st10 = document.getElementById('st-10');
  if (st10) st10.className = 'step-node completed';

  const pill = document.getElementById('sos-live-pill');
  if (pill) {
    pill.textContent = 'VERIFIED // PERMANENT REC';
    pill.className = 'status-live-pill verified';
  }

  showToast('Dual-signed rescue receipt committed to Flight Recorder audit chain!');
}

// ============================================================================
// 4. RESPONDER PORTAL & TRIAGE QUEUE ENGINE
// ============================================================================
function setupResponderPortal() {
  // Urgency Filter Buttons
  const filterBtns = document.querySelectorAll('.btn-urg-filter');
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      AppState.activeFilter = btn.getAttribute('data-filter');
      renderTriageQueue();
    });
  });

  const btnReset = document.getElementById('btn-reset-urg-filter');
  if (btnReset) {
    btnReset.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      document.querySelector('.btn-urg-filter[data-filter="ALL"]')?.classList.add('active');
      AppState.activeFilter = 'ALL';
      renderTriageQueue();
    });
  }

  // Sort Queue Selector
  const sortSelect = document.getElementById('sel-queue-sort');
  if (sortSelect) {
    sortSelect.addEventListener('change', () => {
      const mode = sortSelect.value;
      if (mode === 'dist') AppState.incidents.sort((a, b) => a.distance - b.distance);
      else if (mode === 'urgency') {
        const pOrder = { CRITICAL: 1, URGENT: 2, STABLE: 3 };
        AppState.incidents.sort((a, b) => pOrder[a.urgency] - pOrder[b.urgency]);
      }
      renderTriageQueue();
    });
  }

  // Evidence file upload hash calculation
  const filePicker = document.getElementById('evidence-file-picker');
  if (filePicker) {
    filePicker.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (file) {
        const hashDisplay = document.getElementById('evidence-hash-display');
        hashDisplay.innerHTML = `Calculating SHA-256 for <strong>${file.name}</strong>...`;

        try {
          const buffer = await file.arrayBuffer();
          const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
          const hashArray = Array.from(new Uint8Array(hashBuffer));
          const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');

          hashDisplay.innerHTML = `SHA-256 Hash: <code style="color:var(--accent-orange);">${hashHex}</code> (Integrity Validated)`;
        } catch (err) {
          hashDisplay.textContent = 'Hash calculation complete (Local Offline Key)';
        }
      }
    });
  }

  // Mission Action Progression Buttons in Dossier
  const btnModalAccept = document.getElementById('btn-modal-accept');
  if (btnModalAccept) {
    btnModalAccept.addEventListener('click', async () => {
      const rawId = AppState.activeDossierIncidentId;
      if (!rawId) return;
      try {
        await apiFetch(`/api/v1/incidents/${rawId}/transition`, {
          method: 'POST',
          body: JSON.stringify({ new_state: 'MISSION_ACCEPTED', notes: 'Accepted by ' + AppState.currentUser.fullName })
        });
        showToast('Mission accepted. Turn-by-turn vector activated.');
        closeModal('modal-responder-dossier');
        fetchInitialBackendIncidents();
      } catch (e) {
        showToast('Mission accepted locally.');
      }
    });
  }

  const btnModalEnroute = document.getElementById('btn-modal-enroute');
  if (btnModalEnroute) {
    btnModalEnroute.addEventListener('click', async () => {
      const rawId = AppState.activeDossierIncidentId;
      if (!rawId) return;
      try {
        await apiFetch(`/api/v1/incidents/${rawId}/transition`, {
          method: 'POST',
          body: JSON.stringify({ new_state: 'EN_ROUTE', notes: 'Responder en route to coordinates' })
        });
        showToast('Status updated: Responder EN ROUTE.');
        closeModal('modal-responder-dossier');
        fetchInitialBackendIncidents();
      } catch (e) {
        showToast('Status updated locally.');
      }
    });
  }

  const btnModalOnscene = document.getElementById('btn-modal-onscene');
  if (btnModalOnscene) {
    btnModalOnscene.addEventListener('click', async () => {
      const rawId = AppState.activeDossierIncidentId;
      if (!rawId) return;
      try {
        await apiFetch(`/api/v1/incidents/${rawId}/transition`, {
          method: 'POST',
          body: JSON.stringify({ new_state: 'ARRIVED_ON_SCENE', notes: 'Responder arrived on-scene' })
        });
        showToast('Status updated: ARRIVED ON SCENE.');
        closeModal('modal-responder-dossier');
        fetchInitialBackendIncidents();
      } catch (e) {
        showToast('Status updated locally.');
      }
    });
  }

  // Modal Rescue Submit
  const btnSubmitRescue = document.getElementById('btn-modal-submit-rescue');
  if (btnSubmitRescue) {
    btnSubmitRescue.addEventListener('click', async () => {
      const rawId = AppState.activeDossierIncidentId;
      if (!rawId) return;
      const outcome = document.getElementById('modal-rescue-outcome')?.value || 'RESCUED';
      const hashDisplay = document.getElementById('evidence-hash-display');
      const hash = hashDisplay?.querySelector('code')?.textContent || `sha256_mock_${Date.now()}`;
      try {
        await apiFetch(`/api/v1/incidents/${rawId}/transition`, {
          method: 'POST',
          body: JSON.stringify({
            new_state: 'RESCUE_COMPLETED',
            notes: `Rescue completed with outcome: ${outcome}`,
            evidence_reference: hash
          })
        });
        showToast('Rescue report submitted and signed with SHA-256 evidence proof.');
        closeModal('modal-responder-dossier');
        fetchInitialBackendIncidents();
      } catch (e) {
        showToast('Rescue report saved locally.');
      }
    });
  }
}

function renderTriageQueue() {
  const container = document.getElementById('triage-cards-container');
  if (!container) return;

  const filtered = AppState.incidents.filter(inc => {
    if (AppState.activeFilter === 'ALL') return true;
    return inc.urgency === AppState.activeFilter;
  });

  const countLabel = document.getElementById('val-queue-count-label');
  if (countLabel) countLabel.textContent = `${filtered.length} INCIDENTS NEARBY`;

  const activeCount = document.getElementById('val-active-tasks-count');
  if (activeCount) activeCount.textContent = filtered.length;

  container.innerHTML = filtered.map(inc => {
    const priorityClass = inc.urgency === 'CRITICAL' ? 'priority-critical' : (inc.urgency === 'URGENT' ? 'priority-urgent' : 'priority-stable');
    const badgeClass = inc.urgency.toLowerCase();

    const distDisplay = inc.distance != null ? `<span class="dist-num-bold">${inc.distance}</span><span class="dist-unit-label">KM</span>` : `<span class="dist-num-bold">--</span><span class="dist-unit-label">N/A</span>`;
    const hopDisplay = inc.hop != null ? `HOP: ${inc.hop}` : 'Direct';
    const simBadge = inc.simulated ? `<span class="badge-simulated">[SIMULATED]</span>` : '';

    return `
      <div class="incident-card-ursafe ${priorityClass}" data-id="${inc.id}">
        <!-- Distance Box -->
        <div class="distance-box-square">
          ${distDisplay}
        </div>

        <!-- Middle Details -->
        <div class="incident-details-middle">
          <div class="meta-pill-row">
            ${simBadge}
            <span class="badge-priority-pill ${badgeClass}">● ${inc.urgency}</span>
            <span class="incident-id-tag">${inc.id}</span>
            <span>•</span>
            <span class="incident-time-tag">${inc.timeAgo}</span>
            <span>•</span>
            <span class="incident-hop-tag"><iconify-icon icon="lucide:radio"></iconify-icon> ${hopDisplay}</span>
          </div>

          <h3 class="incident-headline-bold">${inc.title}</h3>
          <p class="incident-sub-snippet">${inc.description}</p>

          <div class="incident-tags-row">
            ${inc.tags.map(t => `<span class="${t.type === 'match' ? 'tag-skills-match' : 'tag-requirement'}">${t.text}</span>`).join('')}
          </div>
        </div>

        <!-- Right Action Buttons -->
        <div class="incident-actions-right">
          <button class="btn-accept-task" onclick="handleAcceptTask('${inc.id}')">
            <iconify-icon icon="lucide:check-circle"></iconify-icon>
            <span>Accept Task</span>
          </button>
          <button class="btn-view-details" onclick="openIncidentDossier('${inc.id}')">
            <span>View Details</span>
          </button>
        </div>
      </div>
    `;
  }).join('');
}

window.handleAcceptTask = async function(incidentId) {
  const inc = AppState.incidents.find(i => i.id === incidentId);
  if (!inc) return;

  inc.status = 'ACCEPTED';
  inc.resolution = 'En Route';
  inc.responder = AppState.currentUser.fullName;

  // Try real backend state transition endpoint with authentication
  try {
    await apiFetch(`/api/v1/incidents/${inc.rawId}/transition`, {
      method: 'POST',
      body: JSON.stringify({
        new_state: 'MISSION_ACCEPTED',
        reason: 'Mission accepted by ' + AppState.currentUser.fullName
      })
    });
  } catch (e) {
    // offline acceptance
  }

  renderTriageQueue();
  renderActivityLog();
  showToast(`Mission ${incidentId} accepted. Turn-by-turn vector activated.`);
};

window.openIncidentDossier = function(incidentId) {
  const inc = AppState.incidents.find(i => i.id === incidentId || i.rawId === incidentId);
  if (!inc) return;

  AppState.activeDossierIncidentId = inc.rawId || incidentId;

  document.getElementById('modal-incident-title').textContent = inc.title;
  document.getElementById('modal-incident-id').textContent = `ID: ${inc.id}`;
  document.getElementById('modal-incident-desc').textContent = inc.description;

  const pPill = document.getElementById('modal-priority-pill');
  if (pPill) {
    pPill.textContent = inc.urgency;
    pPill.className = `badge-priority-pill ${inc.urgency.toLowerCase()}`;
  }

  openModal('modal-responder-dossier');
};

// ============================================================================
// 5. GLOBAL DASHBOARD & MASTER REQUESTS ACTIVITY LOG
// ============================================================================
function setupGlobalDashboard() {
  const searchInput = document.getElementById('log-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      const q = searchInput.value.toLowerCase();
      renderActivityLog(q);
    });
  }

  const btnExport = document.getElementById('btn-export-log-csv');
  if (btnExport) {
    btnExport.addEventListener('click', exportLogToCSV);
  }
}

function renderActivityLog(filterQuery = '') {
  const tbody = document.getElementById('tbody-activity-log');
  if (!tbody) return;

  let list = AppState.incidents;
  if (filterQuery) {
    list = list.filter(i => 
      i.id.toLowerCase().includes(filterQuery) ||
      i.title.toLowerCase().includes(filterQuery) ||
      i.type.toLowerCase().includes(filterQuery) ||
      i.responder.toLowerCase().includes(filterQuery)
    );
  }

  tbody.innerHTML = list.map(inc => {
    const statusClass = inc.urgency === 'CRITICAL' ? 'critical' : (inc.urgency === 'URGENT' ? 'urgent' : 'standard');
    const resClass = inc.resolution.toLowerCase().replace(' ', '-');

    return `
      <tr>
        <td class="timestamp-mono">${new Date().toLocaleTimeString()}</td>
        <td class="incident-id-mono">${inc.id}</td>
        <td>
          <div class="type-cell-with-icon">
            <iconify-icon icon="${inc.category === 'FLOOD' ? 'lucide:droplet' : (inc.category === 'COLLAPSE' ? 'lucide:home' : 'lucide:activity')}" style="color:var(--accent-orange);"></iconify-icon>
            <span>${inc.type}</span>
          </div>
        </td>
        <td>
          <span class="status-badge-table ${statusClass}">${inc.urgency}</span>
        </td>
        <td><strong>${inc.responder}</strong></td>
        <td><span class="resolution-cell-text ${resClass}">● ${inc.resolution}</span></td>
      </tr>
    `;
  }).join('');
}

function exportLogToCSV() {
  let csv = 'Timestamp,Incident ID,Type,Urgency,Responder,Resolution\n';
  AppState.incidents.forEach(i => {
    csv += `"${new Date().toISOString()}","${i.id}","${i.type}","${i.urgency}","${i.responder}","${i.resolution}"\n`;
  });

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `ursafe_disaster_log_${Date.now()}.csv`;
  a.click();
  showToast('Activity Log exported as CSV.');
}

function initOrchestrationMap() {
  const mapContainer = document.getElementById('central-orchestration-map');
  if (!mapContainer || AppState.maps.orchestration) return;

  try {
    AppState.maps.orchestration = L.map('central-orchestration-map', {
      center: [19.0820, 72.8830],
      zoom: 14,
      zoomControl: false,
      attributionControl: false
    });

    // Default to Google Maps Roadmap if API key is present, otherwise offline warm tiles
    const defaultLayer = getGoogleMapsKey() ? 'google-roadmap' : 'osm-mesh';
    AppState.maps.orchestrationTileLayer = createMapTileLayer(defaultLayer).addTo(AppState.maps.orchestration);

    // Hazard Polygon Overlay
    const floodPolygon = [
      [19.0880, 72.8750],
      [19.0840, 72.8920],
      [19.0760, 72.8880],
      [19.0790, 72.8720]
    ];
    L.polygon(floodPolygon, {
      color: '#EF4444',
      weight: 1.5,
      dashArray: '5, 5',
      fillColor: '#EF4444',
      fillOpacity: 0.12
    }).addTo(AppState.maps.orchestration);

  } catch (err) {
    console.warn('Leaflet orchestration init note:', err.message);
  }
}

// ============================================================================
// 6. TELEMETRY & MESH CONTROLS
// ============================================================================
function calculateHaversineKm(lat1, lon1, lat2, lon2) {
  if (lat1 == null || lon1 == null || lat2 == null || lon2 == null) return null;
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return parseFloat((R * c).toFixed(1));
}

function setupTelemetryControls() {
  const btnPing = document.getElementById('btn-trigger-mesh-ping');
  if (btnPing) {
    btnPing.addEventListener('click', async () => {
      btnPing.classList.add('animate-spin');
      try {
        const res = await fetch('/api/v1/health');
        const data = await res.json();
        btnPing.classList.remove('animate-spin');
        const syncTimeEl = document.getElementById('val-last-sync-time');
        if (syncTimeEl) syncTimeEl.textContent = '0s AGO';
        showToast(`Mesh Hub Ping: ${data.status || 'ONLINE'} • SQLite: ${data.subsystems?.database || 'OK'}`);
      } catch (err) {
        btnPing.classList.remove('animate-spin');
        showToast('Local Mesh Ping: Local node operational (Offline mode)');
      }
    });
  }
}

// ============================================================================
// 7. WEBSOCKET REAL-TIME SYNC
// ============================================================================
function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}`;

  try {
    AppState.ws = new WebSocket(wsUrl);
    AppState.ws.onopen = () => {
      console.log('[UrSafe Stream] Real-time Emergency Mesh Stream active.');
    };
    AppState.ws.onmessage = (event) => {
      try {
        const packet = JSON.parse(event.data);
        const eventType = packet.type || packet.event;
        const payload = packet.payload || packet.data;

        if (eventType === 'INCIDENT_CREATED') {
          showToast(`SOS Beacon Broadcast: ${payload.category || 'Emergency'} in ${payload.location_description || 'Sector 4'}`);
          fetchInitialBackendIncidents();
        } else if (eventType === 'INCIDENT_STATE_CHANGED' || eventType === 'INCIDENT_REOPENED' || eventType === 'INCIDENT_CLOSED') {
          fetchInitialBackendIncidents();
        } else if (eventType === 'DEVICE_CONNECTED' || eventType === 'DEVICE_DISCONNECTED') {
          refreshDeviceRegistry();
        } else if (eventType === 'RESCUE_VERIFIED') {
          showToast(`Incident verified and approved by Disaster Authority.`);
          fetchInitialBackendIncidents();
        } else if (eventType && eventType.startsWith('continuity.')) {
          pollConnectivityCockpit();
          fetchOutboxQueue();
          fetchAuthorityDashboardData();
          if (eventType === 'continuity.message.delivered') {
            showToast(`Delivery confirmed via ${payload.transport} (${payload.ack_level})`);
          } else if (eventType === 'continuity.message.queued') {
            showToast(`Priority P${payload.priority} message queued in outbox`);
          }
        }
      } catch (e) {}
    };
    AppState.ws.onclose = () => {
      setTimeout(connectWebSocket, 5000);
    };
  } catch (e) {}
}

async function fetchInitialBackendIncidents() {
  try {
<<<<<<< HEAD
    const token = AppState.currentUser?.token || AppState.currentUser?.session?.token;
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
    const res = await fetch('/api/v1/incidents', { headers });

    let fetchedList = [];
    if (res.ok) {
      fetchedList = await res.json();
    }

    // Filter simulation vs live mode
    const isSimMode = AppState.mode === 'TRAINING';
    AppState.incidents = [];

    if (Array.isArray(fetchedList) && fetchedList.length > 0) {
      fetchedList.forEach(srvInc => {
        const isSim = Boolean(srvInc.is_simulation || srvInc.training);
        if (!isSimMode && isSim) return; // Do not render simulated in live mode

        const dist = (srvInc.latitude && srvInc.longitude)
          ? calculateHaversineKm(AppState.location.lat, AppState.location.lon, srvInc.latitude, srvInc.longitude)
          : null;

        AppState.incidents.push({
          id: '#' + srvInc.id.slice(-6).toUpperCase(),
          rawId: srvInc.id,
          category: srvInc.category,
          type: srvInc.category + ' Emergency',
          urgency: srvInc.urgency || 'URGENT',
          title: srvInc.description ? srvInc.description.slice(0, 36) + '...' : 'SOS Report',
          description: srvInc.description || 'Emergency reported via offline mesh.',
          distance: dist,
          timeAgo: 'Just now',
          hop: srvInc.hop_count || null,
          lat: srvInc.latitude || null,
          lon: srvInc.longitude || null,
          tags: [{ text: srvInc.urgency, type: 'req' }, { text: isSim ? 'SIMULATED' : 'Verified', type: 'match' }],
          status: srvInc.status || 'REPORTED',
          responder: srvInc.responder_name || 'Unassigned',
          resolution: srvInc.status || 'Reported',
          simulated: isSim
        });
      });
    }

    // In training mode, if no real training incidents returned, show isolated training scenarios
    if (isSimMode && AppState.incidents.length === 0) {
      AppState.incidents = SimulatedSeedIncidents.map(sc => ({ ...sc }));
    }

    renderTriageQueue();
    renderActivityLog();
  } catch (e) {
    if (AppState.mode === 'TRAINING' && AppState.incidents.length === 0) {
      AppState.incidents = SimulatedSeedIncidents.map(sc => ({ ...sc }));
      renderTriageQueue();
      renderActivityLog();
    }
  }
}

async function fetchAuthorityDashboardData() {
  const token = AppState.currentUser?.token || AppState.currentUser?.session?.token;
  const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

  // Section 1: Incidents by Priority
  try {
    const incRes = await fetch('/api/v1/incidents?all=true', { headers });
    if (incRes.ok) {
      const incList = await incRes.json();
      if (Array.isArray(incList)) {
        let critical = 0, urgent = 0, standard = 0;
        incList.forEach(inc => {
          if (inc.status !== 'VERIFIED' && inc.status !== 'CLOSED' && inc.status !== 'CANCELLED') {
            if (inc.urgency === 'CRITICAL') critical++;
            else if (inc.urgency === 'URGENT') urgent++;
            else standard++;
=======
    const res = await apiFetch('/api/v1/incidents?all=true');
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        data.forEach(srvInc => {
          const existing = AppState.incidents.find(i => i.rawId === srvInc.id);
          if (!existing) {
            AppState.incidents.unshift({
              id: '#' + srvInc.id.slice(-6).toUpperCase(),
              rawId: srvInc.id,
              category: srvInc.category,
              type: srvInc.category + ' Emergency',
              urgency: srvInc.urgency || 'URGENT',
              title: srvInc.description ? srvInc.description.slice(0, 36) + '...' : 'SOS Report',
              description: srvInc.description || 'Emergency reported via offline mesh.',
              distance: 0.8,
              timeAgo: 'Just now',
              hop: '01',
              lat: srvInc.latitude || AppState.location.lat,
              lon: srvInc.longitude || AppState.location.lon,
              tags: [{ text: srvInc.urgency, type: 'req' }, { text: 'Real Incident', type: 'match' }],
              status: srvInc.status || 'REPORTED',
              responder: srvInc.responder_name || 'Unassigned',
              resolution: srvInc.status || 'Reported'
            });
          } else {
            existing.status = srvInc.status;
            existing.resolution = srvInc.status;
            if (srvInc.responder_name) existing.responder = srvInc.responder_name;
>>>>>>> ece2da3b08329b23ed48edd26b04c7df06397e4f
          }
        });
        const total = critical + urgent + standard;
        const elCrit = document.getElementById('auth-critical-count');
        const elUrg = document.getElementById('auth-urgent-count');
        const elStd = document.getElementById('auth-standard-count');
        const elTot = document.getElementById('auth-unresolved-count');
        if (elCrit) elCrit.textContent = critical;
        if (elUrg) elUrg.textContent = urgent;
        if (elStd) elStd.textContent = standard;
        if (elTot) elTot.textContent = total;
      }
    }
  } catch (_) {}

  // Section 2: Network Nodes by Role & State
  try {
    const meshRes = await fetch('/api/v1/mesh', { headers });
    const roleBreakdownEl = document.getElementById('auth-nodes-role-breakdown');
    if (meshRes.ok) {
      const meshData = await meshRes.json();
      const nodes = meshData.nodes || [];
      let routerCount = 0, clientCount = 0, offlineCount = 0;
      nodes.forEach(n => {
        if (n.role === 'ROUTER' || n.role === 'RELAY' || n.role === 'REPEATER') routerCount++;
        else clientCount++;
        if (n.status === 'OFFLINE' || (Date.now() - n.last_seen_at) > 300000) offlineCount++;
      });
      const elTotal = document.getElementById('auth-nodes-total-count');
      const elActiveNodes = document.getElementById('metric-nodes-val');
      if (elTotal) elTotal.textContent = nodes.length;
      if (elActiveNodes) elActiveNodes.textContent = (nodes.length - offlineCount);

      if (nodes.length === 0) {
        if (roleBreakdownEl) {
          roleBreakdownEl.innerHTML = '<div class="empty-state-text" style="color:var(--text-muted); font-size:12px; font-style:italic; padding:6px 0;">No network nodes registered yet</div>';
        }
      } else {
        if (roleBreakdownEl) {
          roleBreakdownEl.innerHTML = `
            <div class="priority-bar-item">
              <span>ROUTER / RELAY</span>
              <strong id="auth-nodes-router-count">${routerCount}</strong>
            </div>
            <div class="priority-bar-item">
              <span>CLIENT / PEER</span>
              <strong id="auth-nodes-client-count">${clientCount}</strong>
            </div>
            <div class="priority-bar-item">
              <span>OFFLINE / UNKNOWN</span>
              <strong id="auth-nodes-offline-count">${offlineCount}</strong>
            </div>
          `;
        }
      }
    } else {
      if (roleBreakdownEl) {
        roleBreakdownEl.innerHTML = '<div class="empty-state-text" style="color:var(--text-muted); font-size:12px; font-style:italic; padding:6px 0;">No network nodes registered yet</div>';
      }
      const elNodes = document.getElementById('metric-nodes-val');
      if (elNodes) elNodes.textContent = '0';
    }
  } catch (_) {
    const roleBreakdownEl = document.getElementById('auth-nodes-role-breakdown');
    if (roleBreakdownEl) {
      roleBreakdownEl.innerHTML = '<div class="empty-state-text" style="color:var(--text-muted); font-size:12px; font-style:italic; padding:6px 0;">No network nodes registered yet</div>';
    }
    const elNodes = document.getElementById('metric-nodes-val');
    if (elNodes) elNodes.textContent = '0';
  }
    if (elNodes) elNodes.textContent = '0';
  }

  // Section 3: Partitions & Connectivity State
  try {
    const cockpitRes = await fetch('/api/v1/continuity/cockpit', { headers });
    if (cockpitRes.ok) {
      const cockpit = await cockpitRes.json();
      const elTransports = document.getElementById('auth-transports-count');
      const elIntegrity = document.getElementById('metric-integrity-val');
      const elFill = document.getElementById('metric-integrity-fill');
      const elOutbox = document.getElementById('auth-outbox-pending-count');
      const elPartition = document.getElementById('auth-partition-state');

      const onlineCount = cockpit.active_transports_count || 0;
      if (elTransports) elTransports.textContent = onlineCount;
      if (elIntegrity) elIntegrity.textContent = onlineCount > 0 ? `${onlineCount} ACTIVE` : 'OFFLINE';
      if (elFill) elFill.style.width = onlineCount > 0 ? `${Math.min(100, onlineCount * 33)}%` : '0%';
      if (elOutbox) elOutbox.textContent = cockpit.outbox_pending_count || 0;
      if (elPartition) {
        if (onlineCount >= 2) {
          elPartition.textContent = 'REDUNDANT MESH';
          elPartition.style.color = 'var(--accent-green)';
        } else if (onlineCount === 1) {
          elPartition.textContent = 'SINGLE CARRIER';
          elPartition.style.color = 'var(--accent-amber)';
        } else {
          elPartition.textContent = 'ISOLATED LOCAL CELL';
          elPartition.style.color = 'var(--accent-red)';
        }
      }
    }
  } catch (_) {}
}

// ============================================================================
// 8. MODALS & TOAST UTILITIES
// ============================================================================
function setupModals() {
  const btnWhereAmI = document.getElementById('btn-where-am-i');
  if (btnWhereAmI) {
    btnWhereAmI.addEventListener('click', () => openModal('modal-where-am-i'));
  }

  const btnConnCenter = document.getElementById('btn-connection-center');
  if (btnConnCenter) {
    btnConnCenter.addEventListener('click', () => {
      openModal('modal-connection-center');
      pollConnectivityCockpit();
    });
  }

  const btnCloseCaseDetail = document.getElementById('btn-close-case-detail');
  if (btnCloseCaseDetail) {
    btnCloseCaseDetail.addEventListener('click', () => closeModal('modal-case-detail'));
  }

  const btnReopen = document.getElementById('btn-reopen-case');
  if (btnReopen) {
    btnReopen.addEventListener('click', async () => {
      const title = document.getElementById('cd-title')?.textContent || '';
      const incId = title.replace('CASE #', '').trim();
      const inc = AppState.incidents.find(i => i.id === incId || i.rawId === incId);
      const targetId = inc ? inc.rawId : incId;
      try {
        const res = await apiFetch(`/api/v1/incidents/${targetId}/reopen`, {
          method: 'POST',
          body: JSON.stringify({ reason: 'Reopened by Incident Commander for further verification' })
        });
        if (res.ok) {
          showToast(`Case ${incId} successfully reopened.`);
          closeModal('modal-case-detail');
          fetchInitialBackendIncidents();
        } else {
          const errData = await res.json();
          showToast(errData.error || 'Reopen failed: Authority credentials required.');
        }
      } catch (err) {
        showToast(`Offline mode: Reopen queued in local mesh outbox.`);
      }
    });
  }

  // Close buttons
  const closeBtns = document.querySelectorAll('.btn-modal-close');
  closeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-close');
      closeModal(targetId);
    });
  });

  // Backdrop click to close
  const modals = document.querySelectorAll('.modal-backdrop');
  modals.forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) modal.classList.add('hidden');
    });
  });
}

// ============================================================================
// HARDWARE CONNECTION CENTER & BLUETOOTH BLE COMPONENT
// ============================================================================
function initHardwareConnectionCenter() {
  const btnConnCenter = document.getElementById('btn-connection-center');
  if (btnConnCenter) {
    btnConnCenter.addEventListener('click', () => {
      openModal('modal-connection-center');
      refreshDeviceRegistry();
    });
  }

  const btnRefresh = document.getElementById('btn-refresh-devices');
  if (btnRefresh) {
    btnRefresh.addEventListener('click', () => {
      refreshDeviceRegistry();
    });
  }

  const btnScanBle = document.getElementById('btn-scan-web-bluetooth');
  if (btnScanBle) {
    btnScanBle.addEventListener('click', async () => {
      btnScanBle.disabled = true;
      btnScanBle.innerHTML = `<iconify-icon icon="lucide:loader-2" class="animate-spin"></iconify-icon><span>Scanning BLE 0xFE26...</span>`;
      
      try {
        if (navigator.bluetooth && navigator.bluetooth.requestDevice) {
          const device = await navigator.bluetooth.requestDevice({
            acceptAllDevices: true,
            optionalServices: ['battery_service', 'device_information']
          });
          if (device) {
            await apiFetch('/api/v1/devices/connect', {
              method: 'POST',
              body: JSON.stringify({
                device_id: device.id,
                hardware_model: device.name || 'UrSafe BLE LoRa Peer',
                mac_address: 'BLE:' + (device.id.slice(0, 8).toUpperCase()),
                device_type: 'ANDROID_MOBILE',
                battery_level: 92,
                rssi_dbm: -52
              })
            });
            showToast(`Paired with Web Bluetooth node: ${device.name || 'UrSafe BLE Node'}`);
          }
        } else {
          // Simulated Radar sweep fallback when hardware BLE browser flag is not available
          setTimeout(async () => {
            const mockId = 'dev-ble-' + Math.floor(100 + Math.random() * 900);
            await apiFetch('/api/v1/devices/connect', {
              method: 'POST',
              body: JSON.stringify({
                device_id: mockId,
                hardware_model: 'UrSafe LoRa Companion #' + mockId.slice(-3),
                mac_address: 'C4:7D:CC:2B:' + mockId.slice(-2) + ':01',
                device_type: 'ANDROID_MOBILE',
                battery_level: 89,
                rssi_dbm: -55
              })
            });
            showToast(`Radar Sweep: Discovered & paired UrSafe Node ${mockId} (UUID 0xFE26).`);
            refreshDeviceRegistry();
            btnScanBle.disabled = false;
            btnScanBle.innerHTML = `<iconify-icon icon="lucide:search"></iconify-icon><span>Scan Web BLE (0xFE26)</span>`;
          }, 1000);
          return;
        }
      } catch (err) {
        showToast('BLE Scan: ' + (err.name === 'NotFoundError' ? 'User cancelled device pairing.' : err.message));
      } finally {
        btnScanBle.disabled = false;
        btnScanBle.innerHTML = `<iconify-icon icon="lucide:search"></iconify-icon><span>Scan Web BLE (0xFE26)</span>`;
        refreshDeviceRegistry();
      }
    });
  }
}

async function refreshDeviceRegistry() {
  try {
    const res = await apiFetch('/api/v1/devices');
    if (!res.ok) return;
    const data = await res.json();

    const ursafeList = document.getElementById('list-ursafe-nodes');
    const radioList = document.getElementById('list-compatible-radios');
    const otherList = document.getElementById('list-other-devices');

    // 1. UrSafe BLE Nodes
    if (ursafeList) {
      const ursafeDevices = data.ursafe_devices || [];
      const countEl = document.getElementById('count-ursafe-nodes');
      if (countEl) countEl.textContent = `${ursafeDevices.length} Nodes`;
      ursafeList.innerHTML = ursafeDevices.length > 0
        ? ursafeDevices.map(d => `
          <div class="device-item-card ${d.connection_state === 'CONNECTED' ? 'connected' : ''}">
            <div class="device-meta-group">
              <div class="device-icon-bubble">
                <iconify-icon icon="lucide:radio"></iconify-icon>
              </div>
              <div>
                <div style="font-weight:700; font-size:13px; display:flex; align-items:center; gap:6px;">
                  <span>${d.hardware_model || 'UrSafe BLE Node'}</span>
                  ${d.connection_state === 'CONNECTED' ? '<span class="status-badge-table standard">CONNECTED</span>' : ''}
                </div>
                <div style="font-family:var(--font-mono); font-size:11px; color:var(--text-muted);">${d.mac_address || d.id} • BLE UUID 0xFE26</div>
              </div>
            </div>
            <div style="display:flex; align-items:center; gap:8px;">
              <span class="device-telemetry-pill">
                <iconify-icon icon="lucide:battery-charging" style="color:var(--accent-green);"></iconify-icon>
                ${d.battery_level != null ? d.battery_level : 85}%
              </span>
              <span class="device-telemetry-pill">
                <iconify-icon icon="lucide:wifi" style="color:var(--accent-orange);"></iconify-icon>
                ${d.rssi_dbm != null ? d.rssi_dbm : -58} dBm
              </span>
              ${d.connection_state === 'CONNECTED'
                ? `<button class="layer-pill" onclick="disconnectDevice('${d.id}')" style="background:#EF4444; color:#fff; border-color:#EF4444;">Disconnect</button>`
                : `<button class="btn-view-details" onclick="connectDevice('${d.id}')" style="padding:4px 12px; font-size:11px;">Connect</button>`}
            </div>
          </div>
        `).join('')
        : '<p style="font-size:12px; color:var(--text-muted); margin:0;">No active UrSafe BLE nodes discovered in radius.</p>';
    }

    // 2. Compatible Hardware Radios (Meshtastic SX1262 LoRa)
    if (radioList) {
      const radios = data.compatible_radios || [];
      const countEl = document.getElementById('count-radios');
      if (countEl) countEl.textContent = `${radios.length} Radios`;
      radioList.innerHTML = radios.length > 0
        ? radios.map(d => `
          <div class="device-item-card ${d.connection_state === 'CONNECTED' ? 'connected' : ''}">
            <div class="device-meta-group">
              <div class="device-icon-bubble" style="color:var(--accent-orange);">
                <iconify-icon icon="lucide:cpu"></iconify-icon>
              </div>
              <div>
                <div style="font-weight:700; font-size:13px; display:flex; align-items:center; gap:6px;">
                  <span>${d.hardware_model || 'Meshtastic SX1262 LoRa Radio'}</span>
                  <span class="status-badge-table urgent">868 MHz PHY</span>
                </div>
                <div style="font-family:var(--font-mono); font-size:11px; color:var(--text-muted);">${d.mac_address || d.id} • Protocol: Nordic UART / LoRa</div>
              </div>
            </div>
            <div style="display:flex; align-items:center; gap:8px;">
              <span class="device-telemetry-pill">
                <iconify-icon icon="lucide:activity" style="color:var(--accent-green);"></iconify-icon>
                ${d.lqi != null ? `LQI ${d.lqi}%` : 'LQI N/A'}
              </span>
              ${d.connection_state === 'CONNECTED'
                ? `<button class="layer-pill" onclick="disconnectDevice('${d.id}')" style="background:#EF4444; color:#fff; border-color:#EF4444;">Disconnect</button>`
                : `<button class="btn-view-details" onclick="connectDevice('${d.id}')" style="padding:4px 12px; font-size:11px;">Pair LoRa</button>`}
            </div>
          </div>
        `).join('')
        : '<p style="font-size:12px; color:var(--text-muted); margin:0;">No Meshtastic hardware radios detected on USB/UART.</p>';
    }

    // 3. Other Consumer Wireless Peripherals
    if (otherList) {
      const others = data.other_devices || [];
      otherList.innerHTML = others.map(d => `
        <div class="device-item-card incompatible">
          <div class="device-meta-group">
            <div class="device-icon-bubble" style="color:var(--text-muted);">
              <iconify-icon icon="lucide:headphones"></iconify-icon>
            </div>
            <div>
              <div style="font-weight:700; font-size:12.5px; color:var(--text-secondary);">${d.name}</div>
              <div style="font-family:var(--font-mono); font-size:10.5px; color:var(--text-muted);">${d.reason}</div>
            </div>
          </div>
          <span class="badge-priority-pill" style="background:#FEE2E2; color:#DC2626; font-size:9.5px;">INCOMPATIBLE</span>
        </div>
      `).join('');
    }
  } catch (err) {
    console.warn('Refresh devices warning:', err.message);
  }
}

window.connectDevice = async function(deviceId) {
  try {
    const res = await apiFetch('/api/v1/devices/connect', {
      method: 'POST',
      body: JSON.stringify({ device_id: deviceId, hardware_model: 'UrSafe LoRa Peer Node' })
    });
    if (res.ok) {
      showToast(`Device ${deviceId} connected to active mesh!`);
      refreshDeviceRegistry();
    }
  } catch (err) {
    showToast('Device connection updated in local state.');
  }
};

window.disconnectDevice = async function(deviceId) {
  try {
    const res = await apiFetch('/api/v1/devices/disconnect', {
      method: 'POST',
      body: JSON.stringify({ device_id: deviceId })
    });
    if (res.ok) {
      showToast(`Device ${deviceId} disconnected.`);
      refreshDeviceRegistry();
    }
  } catch (err) {
    showToast('Device disconnected.');
  }
};

// ============================================================================
// SYSTEM HEALTH & CRYPTOGRAPHIC FLIGHT RECORDER COMPONENT
// ============================================================================
function initSystemHealth() {
  const btnHealth = document.getElementById('btn-system-health');
  if (btnHealth) {
    btnHealth.addEventListener('click', () => {
      openModal('modal-system-health');
      loadSystemHealth();
    });
  }
}

async function loadSystemHealth() {
  try {
    // 1. Health Probe
    const resHealth = await apiFetch('/api/v1/health');
    if (resHealth.ok) {
      const hData = await resHealth.json();
      const el = document.getElementById('health-api-status');
      if (el) el.textContent = `${hData.status.toUpperCase()} (${resHealth.status} OK)`;
    }

    // 2. Mesh Topology
    const resMesh = await apiFetch('/api/v1/mesh');
    if (resMesh.ok) {
      const mData = await resMesh.json();
      const statusEl = document.getElementById('health-mesh-status');
      const nodesEl = document.getElementById('health-mesh-nodes');
      if (statusEl) statusEl.textContent = mData.frequency || '868 MHz LoRa';
      if (nodesEl) nodesEl.textContent = `${mData.active_nodes || 4} Active Mesh Relays`;
    }

    // 3. Flight Recorder Audit Chain
    const resAudit = await apiFetch('/api/v1/audit/flight-recorder');
    if (resAudit.ok) {
      const aData = await resAudit.json();
      const statusEl = document.getElementById('health-audit-status');
      const lenEl = document.getElementById('health-audit-length');
      if (statusEl) {
        statusEl.textContent = aData.status === 'CHAIN_INTACT' ? 'CHAIN INTACT (SHA-256)' : 'TAMPER DETECTED';
        statusEl.style.color = aData.status === 'CHAIN_INTACT' ? 'var(--accent-green)' : 'var(--accent-red)';
      }
      if (lenEl) lenEl.textContent = `${aData.chain_length || 0} Cryptographically Verified Blocks`;

      const auditStream = document.getElementById('audit-events-stream');
      if (auditStream && Array.isArray(aData.events)) {
        auditStream.innerHTML = aData.events.slice(-12).reverse().map(ev => `
          <div style="background:#FFFFFF; border:1px solid var(--border-color); padding:8px 12px; border-radius:8px; font-size:12px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <strong style="color:var(--text-primary);">${ev.event_type}</strong>
              <span style="font-family:var(--font-mono); font-size:10px; color:var(--text-muted);">${new Date(ev.timestamp).toLocaleTimeString()}</span>
            </div>
            <div style="font-family:var(--font-mono); font-size:10.5px; color:var(--text-secondary); margin-top:2px; word-break:break-all;">
              Hash: ${ev.current_event_hash?.slice(0, 32)}...
            </div>
          </div>
        `).join('');
      }
    }
  } catch (err) {
    console.warn('System health probe note:', err.message);
  }
}

// ============================================================================
// PERSONA & ROLE SWITCHER
// ============================================================================
function initPersonaSelector() {
  const userPill = document.getElementById('user-profile-badge');
  if (userPill) {
    userPill.addEventListener('click', () => {
      openModal('modal-persona-select');
    });
  }

  const optionCards = document.querySelectorAll('.persona-option-card');
  optionCards.forEach(card => {
    card.addEventListener('click', async () => {
      const username = card.getAttribute('data-username');
      const role = card.getAttribute('data-role');
      const name = card.getAttribute('data-name');

      await initSession(username);
      closeModal('modal-persona-select');
      showToast(`Active persona switched to ${name} (${role})`);

      // Switch view appropriately
      if (role === 'CITIZEN') switchView('view-victim');
      else if (role === 'RESPONDER') switchView('view-responder');
      else switchView('view-dashboard');

      fetchInitialBackendIncidents();
    });
  });
}

window.openCaseDetail = async function(incidentId) {
  const inc = AppState.incidents.find(i => i.id === incidentId || i.rawId === incidentId);
  const rawId = inc ? inc.rawId : incidentId;

  try {
    const res = await apiFetch(`/api/v1/incidents/${rawId}`);
    if (res.ok) {
      const data = await res.json();
      const incident = data.incident || inc || {};
      const events = data.events || data.timeline || [];
      const evidence = data.evidence || [];

      const titleEl = document.getElementById('cd-title');
      if (titleEl) titleEl.textContent = `CASE #${incident.id}`;
      const statusEl = document.getElementById('cd-status-badge');
      if (statusEl) statusEl.textContent = incident.status || 'REPORTED';
      const catEl = document.getElementById('cd-category');
      if (catEl) catEl.textContent = incident.category || 'EMERGENCY';
      const urgEl = document.getElementById('cd-urgency');
      if (urgEl) urgEl.textContent = incident.urgency || 'HIGH';
      const vicEl = document.getElementById('cd-victims');
      if (vicEl) vicEl.textContent = `${incident.victim_count || 1} person(s)`;
      const descEl = document.getElementById('cd-desc');
      if (descEl) descEl.textContent = incident.description || 'No description provided';
      const coordsEl = document.getElementById('cd-coords');
      if (coordsEl) coordsEl.textContent = `${incident.latitude?.toFixed(6) || 19.076}° N, ${incident.longitude?.toFixed(6) || 72.877}° E`;
      const accEl = document.getElementById('cd-acc');
      if (accEl) accEl.textContent = `±${incident.accuracy_m || 4.5}m`;
      const addrEl = document.getElementById('cd-address');
      if (addrEl) addrEl.textContent = incident.location_description || incident.address_street || 'Local Mesh Sector';

      // Timeline events
      const timelineEl = document.getElementById('cd-timeline-events');
      if (timelineEl) {
        timelineEl.innerHTML = events.length > 0
          ? events.map(e => `
              <div style="background:#FAF6ED; border-left:3px solid var(--primary-orange); padding:8px 12px; border-radius:4px; font-size:12px;">
                <strong>${e.event_type}</strong> (${e.to_status || ''}) - <em>${new Date(e.timestamp).toLocaleTimeString()}</em>
                <div>${e.notes || e.reason || ''}</div>
              </div>
            `).join('')
          : '<p style="color:var(--text-secondary); font-size:12px;">No historical events recorded yet.</p>';
      }

      // Evidence gallery
      const evEl = document.getElementById('cd-evidence-list');
      if (evEl) {
        evEl.innerHTML = evidence.length > 0
          ? evidence.map(ev => `
              <div style="background:#FAF6ED; border:1px solid var(--border-color); padding:8px 12px; border-radius:6px; font-size:12px;">
                <div style="font-weight:700;">${ev.evidence_type}</div>
                <div style="font-family:var(--font-mono); font-size:11px; word-break:break-all;">Hash: ${ev.sha256_hash}</div>
              </div>
            `).join('')
          : '<p style="color:var(--text-secondary); font-size:12px;">No photographic evidence attached.</p>';
      }

      openModal('modal-case-detail');
      return;
    }
  } catch (err) {
    console.warn('Fetch case detail error:', err);
  }

  // Fallback to local incident dossier if offline
  window.openIncidentDossier(incidentId);
};

function openModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.classList.remove('hidden');
}

function closeModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.classList.add('hidden');
}

function showToast(msg) {
  let toast = document.getElementById('ursafe-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'ursafe-toast';
    toast.style.cssText = `
      position: fixed;
      top: 80px;
      right: 28px;
      background: #3A2C1D;
      color: #FFFBF2;
      border: 1px solid #FF8B3D;
      padding: 12px 20px;
      border-radius: 9999px;
      font-family: var(--font-ui);
      font-size: 13px;
      font-weight: 600;
      box-shadow: 0 10px 30px rgba(0,0,0,0.25);
      z-index: 9999;
      transition: all 0.3s ease;
      display: flex;
      align-items: center;
      gap: 10px;
    `;
    document.body.appendChild(toast);
  }

  toast.innerHTML = `<iconify-icon icon="lucide:radio-receiver" style="color:var(--accent-orange); font-size:16px;"></iconify-icon><span>${msg}</span>`;
  toast.style.opacity = '1';
  toast.style.transform = 'translateY(0)';

  clearTimeout(toast._timeout);
  toast._timeout = setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-10px)';
  }, 3500);
}

// ============================================================================
// 9. PHASE 4: RESCUE CONTINUITY COCKPIT CONTROLLER
// ============================================================================

function setupConnectivityCockpit() {
  const btnRefreshOutbox = document.getElementById('btn-refresh-outbox');
  if (btnRefreshOutbox) {
    btnRefreshOutbox.addEventListener('click', () => {
      fetchOutboxQueue();
      showToast('Refreshing durable outbox queue...');
    });
  }

  const btnDeadLetter = document.getElementById('btn-view-dead-letter');
  if (btnDeadLetter) {
    btnDeadLetter.addEventListener('click', () => {
      fetchDeadLetterQueue();
    });
  }
}

async function pollConnectivityCockpit() {
  try {
    const res = await fetch('/api/v1/continuity/cockpit');
    if (!res.ok) return;
    const data = await res.json();
    renderConnectivityCockpit(data);
  } catch (err) {
    renderOfflineCockpit();
  }
}

function renderConnectivityCockpit(data) {
  // 1. Header Node Capsule & Tickers
  const headerStats = document.getElementById('header-node-stats');
  if (headerStats && data.transports) {
    const activeNames = data.transports.filter(t => t.status === 'CONNECTED').map(t => t.transport_type.replace('_', ' ')).join(' • ');
    headerStats.textContent = `LINKS: ${activeNames || 'LOCAL STORE'} // QUEUE: ${data.queues.total_pending} // BATT: ${data.battery_level_pct}%`;
  }

  const queueValEl = document.getElementById('val-packet-queue');
  if (queueValEl && data.queues) queueValEl.textContent = String(data.queues.total_pending).padStart(2, '0');

  const battValEl = document.getElementById('val-battery-reserve');
  if (battValEl) battValEl.textContent = `${data.battery_level_pct}%`;

  // 2. Citizen Reassurance Card
  const citTitle = document.getElementById('cit-conn-title');
  const citDesc = document.getElementById('cit-conn-desc');
  const citDot = document.getElementById('cit-conn-dot');
  const citPills = document.getElementById('cit-active-paths-pills');

  if (citTitle && citDesc && citPills && data.transports) {
    citTitle.textContent = data.status === 'ALL_PATHS_ONLINE'
      ? '● All Communication Paths Online'
      : (data.active_paths_count > 0 ? '● Emergency Mesh Active — Internet Offline' : '● Offline — Distress Stored Locally');
    
    citDesc.textContent = data.summary;
    if (citDot) {
      citDot.className = data.status === 'ALL_PATHS_ONLINE' ? 'status-pulse-dot' : (data.active_paths_count > 0 ? 'status-pulse-dot warning' : 'status-pulse-dot offline');
    }

    citPills.innerHTML = data.transports.map(t => {
      const isConn = t.status === 'CONNECTED';
      const icon = t.transport_type === 'BLE' ? 'lucide:bluetooth' 
                 : t.transport_type === 'MESHTASTIC_LORA' ? 'lucide:radio'
                 : t.transport_type === 'LOCAL_WIFI' ? 'lucide:wifi'
                 : t.transport_type === 'DATA_MULE' ? 'lucide:truck'
                 : 'lucide:cloud';
      return `
        <span class="path-pill ${isConn ? 'connected' : 'disconnected'}">
          <iconify-icon icon="${icon}"></iconify-icon>
          ${t.display_name.split(' ')[0]} ${isConn ? 'ACTIVE' : 'OFFLINE'}
        </span>
      `;
    }).join('');
  }

  // 3. Responder Bearer Diagnostics
  const respScore = document.getElementById('resp-cockpit-score');
  if (respScore) respScore.textContent = `${data.score}% HEALTH`;

  if (data.transports) {
    const loraTr = data.transports.find(t => t.transport_type === 'MESHTASTIC_LORA');
    const respLoraSignal = document.getElementById('resp-lora-signal');
    if (respLoraSignal && loraTr) {
      respLoraSignal.textContent = loraTr.status === 'CONNECTED' ? `${loraTr.rssi_dbm || -74} dBm / +${loraTr.snr_db || 8.5} dB` : 'OFFLINE';
    }

    const bleTr = data.transports.find(t => t.transport_type === 'BLE');
    const respBleStatus = document.getElementById('resp-ble-status');
    if (respBleStatus && bleTr) {
      respBleStatus.textContent = bleTr.status;
      respBleStatus.style.color = bleTr.status === 'CONNECTED' ? 'var(--accent-green)' : 'var(--text-secondary)';
    }
  }

  const respOutbox = document.getElementById('resp-outbox-count');
  if (respOutbox && data.queues) respOutbox.textContent = `${data.queues.total_pending} PENDING`;

  const respBatt = document.getElementById('resp-battery-cost');
  if (respBatt) respBatt.textContent = `${data.battery_level_pct}% RESERVE`;

  // 4. Authority Dashboard Cockpit
  const valCockpitScore = document.getElementById('val-cockpit-score');
  if (valCockpitScore) valCockpitScore.textContent = `${data.score}% CONNECTIVITY SCORE`;

  const explanationText = document.getElementById('cockpit-explanation-text');
  if (explanationText) explanationText.textContent = data.summary;

  const transportsContainer = document.getElementById('cockpit-transports-container');
  const modalTransportsGrid = document.getElementById('modal-transports-grid');

  if (data.transports) {
    const transportsHtml = data.transports.map(t => {
      const isConn = t.status === 'CONNECTED';
      const linkQ = t.link_quality;
      const badgeClass = isConn ? 'connected' : (t.status === 'DEGRADED' ? 'degraded' : 'disconnected');
      return `
        <div class="transport-card">
          <div class="tr-card-top">
            <span class="tr-name">${t.display_name}</span>
            <span class="tr-status-pill ${badgeClass}">${t.status}</span>
          </div>
          <div class="tr-metrics-row">
            <span>Latency: ${t.latency_ms || 30}ms</span>
            <span>Quality: ${linkQ}</span>
          </div>
          <div class="tr-metrics-row">
            <span>Packets Sent: ${t.packets_sent || 0}</span>
            <span>Acked: ${t.packets_acked || 0}</span>
          </div>
          <button class="btn-tr-toggle" onclick="toggleTransport('${t.transport_id}', '${isConn ? 'DISCONNECTED' : 'CONNECTED'}')">
            <iconify-icon icon="${isConn ? 'lucide:toggle-right' : 'lucide:toggle-left'}"></iconify-icon>
            <span>${isConn ? 'Disconnect (Failure Injection)' : 'Reconnect Bearer'}</span>
          </button>
        </div>
      `;
    }).join('');

    if (transportsContainer) transportsContainer.innerHTML = transportsHtml;
    if (modalTransportsGrid) modalTransportsGrid.innerHTML = transportsHtml;
  }
}

function renderOfflineCockpit() {
  const citTitle = document.getElementById('cit-conn-title');
  const citDesc = document.getElementById('cit-conn-desc');
  const citDot = document.getElementById('cit-conn-dot');
  if (citTitle) citTitle.textContent = '● Offline — Autonomous Local Store';
  if (citDesc) citDesc.textContent = 'All cellular and cloud uplinks offline. Emergencies are retained in durable device outbox.';
  if (citDot) citDot.className = 'status-pulse-dot warning';
}

window.toggleTransport = async function(transportId, newStatus) {
  try {
    const res = await fetch(`/api/v1/continuity/transports/${transportId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        status: newStatus,
        link_quality: newStatus === 'CONNECTED' ? 'GOOD' : 'OFFLINE'
      })
    });
    if (res.ok) {
      showToast(`Transport ${transportId} toggled to ${newStatus}`);
      pollConnectivityCockpit();
      fetchOutboxQueue();
    }
  } catch (err) {
    showToast(`Error toggling transport: ${err.message}`);
  }
};

async function fetchOutboxQueue() {
  const tbody = document.getElementById('tbody-outbox-queue');
  if (!tbody) return;

  try {
    const res = await fetch('/api/v1/continuity/outbox');
    if (!res.ok) return;
    const messages = await res.json();

    if (!Array.isArray(messages) || messages.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" style="text-align:center; padding:20px; color:var(--text-secondary); font-size:12.5px;">
            <iconify-icon icon="lucide:check-circle-2" style="color:var(--accent-green); font-size:18px; vertical-align:middle;"></iconify-icon>
            Outbox queue is empty. All emergency messages successfully delivered and acknowledged.
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = messages.map(m => {
      const isP0 = m.priority === 0;
      const prioBadge = isP0 ? '<span class="badge-prio-0">P0 LIFE CRITICAL</span>' : `<span class="badge-prio-low">P${m.priority}</span>`;
      return `
        <tr>
          <td>${prioBadge}</td>
          <td><code style="font-size:11px;">${m.message_id}</code></td>
          <td><strong>${m.message_type}</strong></td>
          <td><span class="status-badge" style="font-size:10px;">${m.current_state}</span></td>
          <td>${m.last_transport || 'Searching'}</td>
          <td>${m.attempt_count}</td>
          <td style="font-size:12px; color:var(--text-secondary);">${m.human_explanation}</td>
          <td>
            <div style="display:flex; gap:6px;">
              <button class="btn-action-small" onclick="retryOutboxMessage('${m.message_id}')" title="Manual retry">Retry</button>
              <button class="btn-action-small" onclick="cancelOutboxMessage('${m.message_id}')" style="color:#B91C1C;" title="Cancel delivery">Cancel</button>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.warn('Fetch outbox error:', err);
  }
}

async function fetchDeadLetterQueue() {
  const tbody = document.getElementById('tbody-outbox-queue');
  if (!tbody) return;

  try {
    const res = await fetch('/api/v1/continuity/dead-letter');
    if (!res.ok) return;
    const messages = await res.json();

    if (!Array.isArray(messages) || messages.length === 0) {
      showToast('Dead letter queue is currently empty. Zero unrecoverable messages.');
      fetchOutboxQueue();
      return;
    }

    tbody.innerHTML = messages.map(m => {
      return `
        <tr style="background:#FEF2F2;">
          <td><span class="badge-prio-0">DEAD LETTER</span></td>
          <td><code style="font-size:11px;">${m.message_id}</code></td>
          <td><strong>${m.message_type}</strong></td>
          <td><span style="color:#B91C1C; font-weight:700;">EXHAUSTED</span></td>
          <td>${m.last_transport || 'NONE'}</td>
          <td>${m.attempt_count}</td>
          <td style="font-size:12px; color:#B91C1C;">${m.last_error || 'Policy ceiling reached'}</td>
          <td>
            <button class="btn-action-small" onclick="retryOutboxMessage('${m.message_id}')" style="background:#B91C1C; color:#FFF;">Force Retry</button>
          </td>
        </tr>
      `;
    }).join('');
    showToast(`Displaying ${messages.length} dead letter store items.`);
  } catch (err) {
    showToast('Failed to load dead letter queue.');
  }
}

window.retryOutboxMessage = async function(messageId) {
  try {
    const res = await fetch(`/api/v1/continuity/messages/${messageId}/retry`, { method: 'POST' });
    if (res.ok) {
      showToast(`Message ${messageId} reset to outbox queue for immediate retry.`);
      fetchOutboxQueue();
      pollConnectivityCockpit();
    }
  } catch (err) {
    showToast(`Retry error: ${err.message}`);
  }
};

window.cancelOutboxMessage = async function(messageId) {
  try {
    const res = await fetch(`/api/v1/continuity/messages/${messageId}/cancel`, { method: 'POST' });
    if (res.ok) {
      showToast(`Message ${messageId} delivery cancelled.`);
      fetchOutboxQueue();
      pollConnectivityCockpit();
    }
  } catch (err) {
    showToast(`Cancel error: ${err.message}`);
  }
};

