// ─── Helpers ────────────────────────────────────────────────────────────────

async function fetchJSON(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

function getResults(payload) {
  return Array.isArray(payload) ? payload : (payload?.results ?? []);
}

function fmt(v, digits = 1) {
  if (v === null || v === undefined || v === '') return '--';
  const n = Number(v);
  return Number.isNaN(n) ? '--' : n.toFixed(digits);
}

// ─── State ──────────────────────────────────────────────────────────────────

const state = {
  regions: [],
  stations: [],
  activeRegionId: '',
  activeStationId: '',
  activeHours: 24,
  map: null,
  markers: {},
  charts: {}
};

// Expose state for tabs.js
window.getDashboardState = () => ({
  region:  state.activeRegionId,
  station: state.activeStationId,
  period:  String(state.activeHours)
});

// ─── Map ────────────────────────────────────────────────────────────────────

function initMap() {
  const el = document.getElementById('map');
  if (!el || typeof L === 'undefined') return;
  state.map = L.map(el, { scrollWheelZoom: false }).setView([-18.88, 47.51], 5);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '© OpenStreetMap'
  }).addTo(state.map);
  window.dashboardMap = state.map;
}

function clearMarkers() {
  Object.values(state.markers).forEach(m => m.remove());
  state.markers = {};
}

function addStationMarker(station) {
  if (!state.map || state.markers[station.id]) return;
  const marker = L.circleMarker([station.latitude, station.longitude], {
    radius: 8, fillColor: '#4ba3ff', color: '#fff', weight: 1, fillOpacity: 0.9
  }).addTo(state.map);

  marker.bindPopup(`<strong>${station.nom_station}</strong><br>${station.region_name || ''}`);

  marker.on('click', () => {
    const sel = document.getElementById('stationSelect');
    if (sel) {
      sel.value = station.id;
      sel.dispatchEvent(new Event('change'));
    }
  });

  state.markers[station.id] = marker;
}

function fitMap(stations) {
  if (!stations.length || !state.map) return;
  const bounds = L.latLngBounds(stations.map(s => [s.latitude, s.longitude]));
  state.map.fitBounds(bounds.pad(0.25));
}

// ─── Metric cards ───────────────────────────────────────────────────────────

function setMetric(id, v, digits) {
  const el = document.getElementById(id);
  if (el) el.textContent = fmt(v, digits);
}

function updateMetrics(row, isHourly) {
  if (isHourly) {
    setMetric('metricTemp',     row.temperature_2m);
    setMetric('metricRain',     row.precipitation);
    setMetric('metricHumidity', row.relative_humidity_2m);
    setMetric('metricWind',     row.wind_speed_10m);
    setMetric('metricPressure', row.surface_pressure, 0);
  } else {
    setMetric('metricTemp',     row.temperature_avg);
    setMetric('metricRain',     row.precipitation_sum);
    setMetric('metricHumidity', row.relative_humidity_avg);
    setMetric('metricWind',     row.wind_speed_avg);
    setMetric('metricPressure', null);
  }
}

// ─── Charts ─────────────────────────────────────────────────────────────────

function buildChart(id, labels, values, cfg) {
  const canvas = document.getElementById(id);
  if (!canvas) return;
  if (state.charts[id]) state.charts[id].destroy();
  state.charts[id] = new Chart(canvas.getContext('2d'), {
    type: cfg.type,
    data: {
      labels,
      datasets: [{
        label: cfg.label,
        data: values,
        borderColor: cfg.color,
        backgroundColor: cfg.bg ?? 'transparent',
        tension: 0.35,
        fill: !!cfg.bg,
        pointRadius: 2,
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: '#8ea2c2' }, grid: { color: 'rgba(255,255,255,0.04)' } },
        y: { ticks: { color: '#8ea2c2' }, grid: { color: 'rgba(255,255,255,0.04)' } }
      }
    }
  });
}

function renderHourlyCharts(rows) {
  const rev    = [...rows].reverse();
  const labels = rev.map(r => new Date(r.date_heure || r.date).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }));

  buildChart('tempChart',     labels, rev.map(r => +r.temperature_2m    || 0), { type: 'line', label: 'Température',  color: '#4ba3ff', bg: 'rgba(75,163,255,0.20)'   });
  buildChart('rainChart',     labels, rev.map(r => +r.precipitation      || 0), { type: 'bar',  label: 'Pluie',        color: '#48d6d2', bg: 'rgba(72,214,210,0.35)'    });
  buildChart('humidityChart', labels, rev.map(r => +r.relative_humidity_2m || 0), { type: 'line', label: 'Humidité',    color: '#7ce38b', bg: 'rgba(124,227,139,0.18)'  });
  buildChart('windChart',     labels, rev.map(r => +r.wind_speed_10m     || 0), { type: 'line', label: 'Vent',         color: '#f4c86b', bg: 'rgba(244,200,107,0.18)'  });
  buildChart('pressureChart', labels, rev.map(r => +r.surface_pressure   || 0), { type: 'line', label: 'Pression',     color: '#a78bfa', bg: 'rgba(167,139,250,0.18)'  });
  updateMetrics(rows[0], true);
}

async function renderDailyFallback() {
  if (!state.activeStationId) return;
  const daily = getResults(
    await fetchJSON(`/weather-stations/${state.activeStationId}/daily-trend/?days=7`).catch(() => [])
  );
  if (!daily.length) return;
  const rows   = [...daily].reverse();
  const labels = rows.map(r => r.date);

  buildChart('tempChart',     labels, rows.map(r => +r.temperature_avg   || 0), { type: 'line', label: 'Température moy.', color: '#4ba3ff', bg: 'rgba(75,163,255,0.20)'  });
  buildChart('rainChart',     labels, rows.map(r => +r.precipitation_sum || 0), { type: 'bar',  label: 'Pluie',             color: '#48d6d2', bg: 'rgba(72,214,210,0.35)'   });
  buildChart('humidityChart', labels, rows.map(r => +r.relative_humidity_avg || 0), { type: 'line', label: 'Humidité',     color: '#7ce38b', bg: 'rgba(124,227,139,0.18)' });
  buildChart('windChart',     labels, rows.map(r => +r.wind_speed_avg    || 0), { type: 'line', label: 'Vent moy.',         color: '#f4c86b', bg: 'rgba(244,200,107,0.18)' });
  buildChart('pressureChart', labels, rows.map(() => null),                      { type: 'line', label: 'Pression',         color: '#a78bfa'                               });
  updateMetrics(rows[0], false);
}

// ─── Sidebar ─────────────────────────────────────────────────────────────────

function renderStationInfo(station, region) {
  const box = document.getElementById('stationInfo');
  if (!box) return;
  if (!station) { box.innerHTML = '<p>Sélectionnez une station.</p>'; return; }
  const regionName = region?.nom_region || station.region_name || 'Région inconnue';
  box.innerHTML = `
    <div class="station-pill">${station.nom_station}</div>
    <p><strong>Région:</strong> ${regionName}</p>
    <p><strong>Coords:</strong> ${fmt(station.latitude, 4)}, ${fmt(station.longitude, 4)}</p>
    <p><strong>Altitude:</strong> ${fmt(station.altitude, 0)} m</p>
    <p><strong>Timezone:</strong> ${station.timezone || 'N/A'}</p>
  `;
}

function renderAlerts(alerts) {
  const list = document.getElementById('alertsList');
  if (!list) return;
  list.innerHTML = alerts.length
    ? alerts.map(a => `<li><strong>${a.niveau || 'INFO'}</strong> · ${a.type_alerte || ''}<br><span>${a.message || ''}</span></li>`).join('')
    : '<li>Aucune alerte active.</li>';
}

function renderReport(report) {
  const el = document.getElementById('reportData');
  if (el) el.textContent = report?.summary_text || 'Aucun rapport disponible.';
}

function setLastRefresh() {
  const el = document.getElementById('lastRefreshLabel');
  if (el) el.textContent = `Dernière mise à jour: ${new Date().toLocaleString('fr-FR')}`;
}

// ─── Data loading ───────────────────────────────────────────────────────────

async function loadRegionsAndStations() {
  const [regionsPayload, stationsPayload] = await Promise.all([
    fetchJSON('/regions/'),
    fetchJSON('/weather-stations/')
  ]);

  state.regions  = getResults(regionsPayload);
  state.stations = getResults(stationsPayload).map(s => {
    const regionId   = typeof s.region === 'object' ? s.region?.id   : s.region;
    const regionName = typeof s.region === 'object' ? s.region?.nom_region : s.region_name;
    return { ...s, region: regionId, region_name: regionName };
  });

  // Populate region select
  const regionSelect = document.getElementById('regionSelect');
  regionSelect.innerHTML = '<option value="">Toutes les régions</option>';
  state.regions.forEach(r => {
    const opt = document.createElement('option');
    opt.value = r.id;
    opt.textContent = r.nom_region;
    regionSelect.appendChild(opt);
  });

  clearMarkers();
  state.stations.forEach(addStationMarker);

  fillStationSelect();

  if (state.stations.length) {
    state.activeStationId = String(state.stations[0].id);
    state.activeRegionId  = state.stations[0].region ? String(state.stations[0].region) : '';
    document.getElementById('stationSelect').value = state.activeStationId;
    regionSelect.value = state.activeRegionId;
    fitMap(state.stations);
  }
}

function fillStationSelect() {
  const sel      = document.getElementById('stationSelect');
  const filtered = state.stations.filter(s =>
    !state.activeRegionId || String(s.region) === String(state.activeRegionId)
  );

  sel.innerHTML = filtered.length
    ? filtered.map(s => `<option value="${s.id}">${s.nom_station}</option>`).join('')
    : '<option value="">Aucune station</option>';

  state.activeStationId = filtered.length ? String(filtered[0].id) : '';
  sel.value = state.activeStationId;
}

async function loadDashboardData() {
  if (!state.activeStationId) {
    renderStationInfo(null, null);
    renderAlerts([]);
    renderReport(null);
    return;
  }

  const station = state.stations.find(s => String(s.id) === String(state.activeStationId));
  const region  = state.regions.find(r  => String(r.id) === String(state.activeRegionId || station?.region));
  renderStationInfo(station, region);

  const [current, hourly, report, alerts] = await Promise.all([
    fetchJSON(`/weather-stations/${state.activeStationId}/current/`).catch(() => null),
    fetchJSON(`/weather-stations/${state.activeStationId}/hourly-history/?hours=${state.activeHours}`).catch(() => []),
    fetchJSON(`/weather-stations/${state.activeStationId}/report-today/`).catch(() => null),
    fetchJSON(`/weather-stations/${state.activeStationId}/active-alerts/`).catch(() => [])
  ]);

  const rows = getResults(hourly);
  if (rows.length) {
    renderHourlyCharts(rows);
  } else {
    await renderDailyFallback();
  }

  // Override metrics with /current/ if available
  if (current && Object.keys(current).length) {
    setMetric('metricTemp',     current.temperature_2m);
    setMetric('metricRain',     current.precipitation);
    setMetric('metricHumidity', current.relative_humidity_2m);
    setMetric('metricWind',     current.wind_speed_10m);
    setMetric('metricPressure', current.surface_pressure, 0);
  }

  renderReport(report);
  renderAlerts(getResults(alerts));
  setLastRefresh();
}

// ─── Events ──────────────────────────────────────────────────────────────────

function bindEvents() {
  document.getElementById('regionSelect').addEventListener('change', async e => {
    state.activeRegionId = e.target.value;
    fillStationSelect();
    const filtered = state.stations.filter(s =>
      !state.activeRegionId || String(s.region) === String(state.activeRegionId)
    );
    if (filtered.length) fitMap(filtered);
    await loadDashboardData();
  });

  document.getElementById('stationSelect').addEventListener('change', async e => {
    state.activeStationId = e.target.value;
    const s = state.stations.find(s => String(s.id) === String(state.activeStationId));
    if (s?.region) {
      state.activeRegionId = String(s.region);
      const r = document.getElementById('regionSelect');
      if (r) r.value = state.activeRegionId;
    }
    await loadDashboardData();
  });

  document.getElementById('periodSelect').addEventListener('change', async e => {
    state.activeHours = Number(e.target.value);
    await loadDashboardData();
  });

  document.getElementById('refreshButton').addEventListener('click', loadDashboardData);
}

// ─── Boot ────────────────────────────────────────────────────────────────────

window.addEventListener('DOMContentLoaded', async () => {
  initMap();
  bindEvents();
  await loadRegionsAndStations();
  await loadDashboardData();
});