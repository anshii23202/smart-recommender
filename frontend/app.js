const API = 'http://localhost:5000';
let currentUser = null;

// ─── AUTH ───────────────────────────────────────────

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

  if (!name || !email || !password) {
    errEl.textContent = 'Please fill in all fields.'; return;
  }

  const res  = await fetch(`${API}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password })
  });
  const data = await res.json();

  if (data.success) {
    currentUser = data;
    showApp();
  } else {
    errEl.textContent = data.message;
  }
}

async function handleLogin() {
  const email    = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;
  const errEl    = document.getElementById('login-error');

  if (!email || !password) {
    errEl.textContent = 'Please fill in all fields.'; return;
  }

  const res  = await fetch(`${API}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const data = await res.json();

  if (data.success) {
    currentUser = data;
    showApp();
  } else {
    errEl.textContent = data.message;
  }
}

function handleLogout() {
  currentUser = null;
  document.getElementById('app-screen').style.display  = 'none';
  document.getElementById('auth-screen').style.display = 'flex';
  document.getElementById('results').innerHTML = '';
}

function showApp() {
  document.getElementById('auth-screen').style.display = 'none';
  document.getElementById('app-screen').style.display  = 'block';
  document.getElementById('welcome-msg').textContent   = `Hi, ${currentUser.name} 👋`;
}

// ─── RECOMMENDATIONS ────────────────────────────────

async function getRecommendations() {
  const mood   = document.getElementById('mood').value;
  const status = document.getElementById('status-msg');
  const results = document.getElementById('results');

  status.textContent = '📍 Getting your location...';
  results.innerHTML  = '';

  navigator.geolocation.getCurrentPosition(async (pos) => {
    const { latitude, longitude } = pos.coords;
    status.textContent = '🔍 Finding best places near you...';

    const res   = await fetch(`${API}/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lat: latitude,
        lon: longitude,
        mood,
        user_id: currentUser.user_id
      })
    });
    const data = await res.json();
    status.textContent = '';
    if (data.weather) {
        status.textContent = data.weather.weather_tip;
    }
    const places = data.places;

    if (!places || places.length === 0) {
      status.textContent = '😕 No places found nearby. Try a different mood.';
      return;
    }

    // Save each recommendation as a visit
    places.forEach(p => {
      fetch(`${API}/visit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id:    currentUser.user_id,
          place_id:   p.id,
          place_name: p.name,
          mood
        })
      });
    });

    displayPlaces(places, mood);

  }, () => {
    status.textContent = '❌ Location access denied. Please allow location in your browser.';
  });
}

function displayPlaces(places, mood) {
  const results = document.getElementById('results');

  // Group places by cluster
  const clusters = {};
  places.forEach(p => {
    const key = p.cluster_name || 'Places';
    if (!clusters[key]) {
      clusters[key] = {
        emoji:  p.cluster_emoji || '📍',
        places: []
      };
    }
    clusters[key].places.push(p);
  });

  // Render each cluster as a section
  results.innerHTML = Object.entries(clusters).map(([name, group]) => `
    <div class="cluster-section">
      <h2 class="cluster-title">${group.emoji} ${name}</h2>
      <div class="cluster-grid">
        ${group.places.map(p => `
          <div class="card">
            <div class="card-header">
              <h3>${p.name}</h3>
              <span class="badge">${p.category}</span>
            </div>
            <p class="card-meta">📍 ${p.distance_km} km away</p>
            <p class="card-meta">🏠 ${p.address}</p>
            <div class="stars" id="stars-${p.id}">
              <span>Rate: </span>
              ${[1,2,3,4,5].map(n =>
                `<span class="star" onclick="ratePlace('${p.id}','${p.name}',${n})">☆</span>`
              ).join('')}
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `).join('');
}

// ─── RATING ─────────────────────────────────────────

async function ratePlace(placeId, placeName, rating) {
  await fetch(`${API}/rate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id:    currentUser.user_id,
      place_id:   placeId,
      place_name: placeName,
      rating
    })
  });

  // Fill stars visually up to selected rating
  const stars = document.querySelectorAll(`#stars-${placeId} .star`);
  stars.forEach((s, i) => {
    s.textContent = i < rating ? '⭐' : '☆';
  });
}

// ─── HISTORY ────────────────────────────────────────

async function showHistory() {
  const results = document.getElementById('results');
  const status  = document.getElementById('status-msg');

  status.textContent = 'Loading your history...';

  const res    = await fetch(`${API}/history/${currentUser.user_id}`);
  const places = await res.json();

  status.textContent = '';

  if (places.length === 0) {
    results.innerHTML = '<p class="status-msg">You have no visit history yet. Find some places first!</p>';
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

async function trainModel() {
  const status = document.getElementById('status-msg');
  status.textContent = '🧠 Training model on your ratings...';

  const res  = await fetch(`${API}/train`, { method: 'POST' });
  const data = await res.json();

  status.textContent = data.message;
}