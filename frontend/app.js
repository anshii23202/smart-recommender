const API = 'http://localhost:5000';
let currentUser  = null;
let currentPlaces = [];
let map          = null;
let markers      = [];

// ─── AUTH ────────────────────────────────────────────

function showTab(tab) {
  document.getElementById('login-form').style.display    = tab === 'login'    ? 'flex' : 'none';
  document.getElementById('register-form').style.display = tab === 'register' ? 'flex' : 'none';
  document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
}

async function handleRegister() {
  const name     = document.getElementById('reg-name').value.trim();
  const email    = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-password').value;
  const errEl    = document.getElementById('reg-error');
  if (!name || !email || !password) { errEl.textContent = 'Please fill in all fields.'; return; }
  const res  = await fetch(`${API}/register`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password })
  });
  const data = await res.json();
  if (data.success) { currentUser = data; showApp(); }
  else errEl.textContent = data.message;
}

async function handleLogin() {
  const email    = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;
  const errEl    = document.getElementById('login-error');
  if (!email || !password) { errEl.textContent = 'Please fill in all fields.'; return; }
  const res  = await fetch(`${API}/login`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const data = await res.json();
  if (data.success) { currentUser = data; showApp(); }
  else errEl.textContent = data.message;
}

function handleLogout() {
  currentUser = null;
  document.getElementById('app-screen').style.display  = 'none';
  document.getElementById('auth-screen').style.display = 'flex';
  document.getElementById('results').innerHTML = '';
  currentPlaces = [];
}

function showApp() {
  document.getElementById('auth-screen').style.display = 'none';
  document.getElementById('app-screen').style.display  = 'block';
  document.getElementById('welcome-msg').textContent   = `Hi, ${currentUser.name} 👋`;
}

// ─── VIEW TOGGLE ─────────────────────────────────────

function switchView(view) {
  document.getElementById('list-view').style.display = view === 'list' ? 'block' : 'none';
  document.getElementById('map-view').style.display  = view === 'map'  ? 'block' : 'none';
  document.getElementById('btn-list').classList.toggle('active', view === 'list');
  document.getElementById('btn-map').classList.toggle('active',  view === 'map');

  if (view === 'map' && currentPlaces.length > 0) {
    setTimeout(() => showMap(currentPlaces), 100);
  }
}

// ─── RECOMMENDATIONS ─────────────────────────────────

async function getRecommendations() {
  const mood    = document.getElementById('mood').value;
  const status  = document.getElementById('status-msg');
  const results = document.getElementById('results');

  status.textContent = '📍 Getting your location...';
  results.innerHTML  = '';

  navigator.geolocation.getCurrentPosition(async (pos) => {
    const { latitude, longitude } = pos.coords;
    status.textContent = '🔍 Finding best places near you...';

    const res    = await fetch(`${API}/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lat: latitude, lon: longitude,
        mood, user_id: currentUser.user_id
      })
    });
    const data   = await res.json();
    status.textContent = data.weather ? data.weather.weather_tip : '';

    const places = data.places;
    if (!places || places.length === 0) {
      status.textContent = '😕 No places found nearby. Try a different mood.';
      return;
    }

    currentPlaces = places;

    // Save visits silently
    places.forEach(p => fetch(`${API}/visit`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: currentUser.user_id, place_id: p.id, place_name: p.name, mood })
    }));

    displayPlaces(places, mood);

  }, () => {
    status.textContent = '❌ Location access denied. Please allow location in your browser.';
  });
}

// ─── LIST VIEW ───────────────────────────────────────

function displayPlaces(places, mood) {
  const results = document.getElementById('results');

  const clusters = {};
  places.forEach(p => {
    const key = p.cluster_name || 'Places';
    if (!clusters[key]) clusters[key] = { emoji: p.cluster_emoji || '📍', places: [] };
    clusters[key].places.push(p);
  });

  results.innerHTML = Object.entries(clusters).map(([name, group]) => `
    <div class="cluster-section">
      <h2 class="cluster-title">${group.emoji} ${name}</h2>
      <div class="cluster-grid">
        ${group.places.map(p => `
          <div class="card" onclick="focusPlace(${p.lat}, ${p.lon}, '${p.name}')">
            <div class="card-header">
              <h3>${p.name}</h3>
              <span class="badge">${p.category}</span>
            </div>
            <p class="card-meta">📍 ${p.distance_km} km away</p>
            <p class="card-meta">🏠 ${p.address}</p>
            <div class="stars" id="stars-${p.id}">
              <span>Rate: </span>
              ${[1,2,3,4,5].map(n =>
                `<span class="star" onclick="event.stopPropagation();ratePlace('${p.id}','${p.name}',${n})">☆</span>`
              ).join('')}
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `).join('');
}

// ─── MAP VIEW ────────────────────────────────────────

// Pin colours per cluster
const CLUSTER_COLOURS = {
  'Dining':    '#D85A30',
  'Cafes':     '#1D9E75',
  'Outdoors':  '#533AB7',
  'Fast Food': '#BA7517',
};

function makeIcon(colour) {
  return L.divIcon({
    className: '',
    html: `<div style="
      width:32px; height:32px;
      background:${colour};
      border-radius:50% 50% 50% 0;
      transform:rotate(-45deg);
      border:2px solid white;
      box-shadow:0 2px 6px rgba(0,0,0,0.3)">
    </div>`,
    iconSize:   [32, 32],
    iconAnchor: [16, 32],
    popupAnchor:[0, -34]
  });
}

function showMap(places) {
  const mapDiv = document.getElementById('map');
  if (!mapDiv) return;

  // Initialise map once
  if (!map) {
    map = L.map('map').setView([places[0].lat, places[0].lon], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);
  } else {
    // Clear old markers
    markers.forEach(m => map.removeLayer(m));
    markers = [];
    map.setView([places[0].lat, places[0].lon], 14);
  }

  // Add a pin for each place
  places.forEach(p => {
    const colour = CLUSTER_COLOURS[p.cluster_name] || '#378ADD';
    const marker = L.marker([p.lat, p.lon], { icon: makeIcon(colour) })
      .addTo(map)
      .bindPopup(`
        <div style="min-width:160px">
          <strong>${p.name}</strong><br>
          ${p.cluster_emoji || '📍'} ${p.cluster_name || p.category}<br>
          📍 ${p.distance_km} km away<br>
          ⭐ ${p.rating || 'N/A'}
        </div>
      `);
    markers.push(marker);
  });

  // Force map to recalculate size (fixes grey tile bug)
  setTimeout(() => map.invalidateSize(), 150);
}

function focusPlace(lat, lon, name) {
  switchView('map');
  setTimeout(() => {
    if (map) {
      map.setView([lat, lon], 17);
      markers.forEach(m => {
        if (m.getPopup().getContent().includes(name)) m.openPopup();
      });
    }
  }, 200);
}

// ─── RATING ──────────────────────────────────────────

async function ratePlace(placeId, placeName, rating) {
  await fetch(`${API}/rate`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: currentUser.user_id, place_id: placeId, place_name: placeName, rating })
  });
  const stars = document.querySelectorAll(`#stars-${placeId} .star`);
  stars.forEach((s, i) => { s.textContent = i < rating ? '⭐' : '☆'; });
}

// ─── HISTORY ─────────────────────────────────────────

async function showHistory() {
  const results = document.getElementById('results');
  const status  = document.getElementById('status-msg');
  status.textContent = 'Loading your history...';
  const res    = await fetch(`${API}/history/${currentUser.user_id}`);
  const places = await res.json();
  status.textContent = '';
  if (places.length === 0) {
    results.innerHTML = '<p class="status-msg">No visit history yet. Find some places first!</p>';
    return;
  }
  results.innerHTML = `
    <h2 style="margin-bottom:16px">Your visit history</h2>
    ${places.map(p => `
      <div class="card history-card">
        <h3>${p.place_name}</h3>
        <p class="card-meta">🎭 Mood: ${p.mood} &nbsp;|&nbsp; 🕐 ${new Date(p.visited_at).toLocaleDateString()}</p>
      </div>
    `).join('')}
  `;
}

// ─── TRAIN ML ────────────────────────────────────────

async function trainModel() {
  const status = document.getElementById('status-msg');
  status.textContent = '🧠 Training model on your ratings...';
  const res  = await fetch(`${API}/train`, { method: 'POST' });
  const data = await res.json();
  status.textContent = data.message;
}