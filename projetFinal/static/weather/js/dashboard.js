async function fetchJSON(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

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

function getResults(payload) {
  return Array.isArray(payload) ? payload : (payload?.results || []);
}

function formatNumber(value, digits = 1) {
  if (value === null || value === undefined || value === '') {
    return '--';
  }
  const parsed = Number(value);
  return Number.isNaN(parsed) ? '--' : parsed.toFixed(digits);
}

function setLastRefresh() {
  const el = document.getElementById('lastRefreshLabel');
  el.textContent = `Dernière mise à jour: ${new Date().toLocaleString('fr-FR')}`;
}

function initMap() {
  state.map = L.map('map', { scrollWheelZoom: false }).setView([-18.8792, 47.5079], 5);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '&copy; OpenStreetMap'
  }).addTo(state.map);
  // expose for other scripts
  window.dashboardMap = state.map;
}

function clearMarkers() {
  Object.values(state.markers).forEach((marker) => marker.remove());
  state.markers = {};
}

function addStationMarker(station) {
  if (!state.map || state.markers[station.id]) {
    return;
  }
  const marker = L.marker([station.latitude, station.longitude])
    .addTo(state.map)
    .bindPopup(`<strong>${station.nom_station}</strong><br>${station.region_name || ''}`);
  state.markers[station.id] = marker;
}

function fitMapToStations(stations) {
  if (!stations.length || !state.map) {
    return;
  }
  const bounds = L.latLngBounds(stations.map((station) => [station.latitude, station.longitude]));
  state.map.fitBounds(bounds.pad(0.25));
}

function updateMetricCards(hourly) {
  const latest = hourly[0] || {};
  document.getElementById('metricTemp').textContent = formatNumber(latest.temperature_2m);
  document.getElementById('metricRain').textContent = formatNumber(latest.precipitation);
  document.getElementById('metricHumidity').textContent = formatNumber(latest.relative_humidity_2m);
  document.getElementById('metricWind').textContent = formatNumber(latest.wind_speed_10m);
  document.getElementById('metricPressure').textContent = formatNumber(latest.surface_pressure, 0);
}

function updateMetricCardsFromDaily(daily) {
  const latest = daily[0] || {};
  document.getElementById('metricTemp').textContent = formatNumber(latest.temperature_avg);
  document.getElementById('metricRain').textContent = formatNumber(latest.precipitation_sum);
  document.getElementById('metricHumidity').textContent = formatNumber(latest.relative_humidity_avg);
  document.getElementById('metricWind').textContent = formatNumber(latest.wind_speed_avg);
  document.getElementById('metricPressure').textContent = '--';
}

function renderStationInfo(station, region) {
  const box = document.getElementById('stationInfo');
  if (!station) {
    box.innerHTML = '<p>Sélectionnez une station.</p>';
    return;
  }
  const regionName = region?.nom_region || station.region_name || 'Région inconnue';
  box.innerHTML = `
    <div class="station-pill">${station.nom_station}</div>
    <p><strong>Région:</strong> ${regionName}</p>
    <p><strong>Coordonnées:</strong> ${formatNumber(station.latitude, 4)}, ${formatNumber(station.longitude, 4)}</p>
    <p><strong>Altitude:</strong> ${formatNumber(station.altitude, 0)} m</p>
    <p><strong>Timezone:</strong> ${station.timezone || 'N/A'}</p>
  `;
}

function renderAlerts(alerts) {
  const list = document.getElementById('alertsList');
  if (!alerts.length) {
    list.innerHTML = '<li>Aucune alerte active.</li>';
    return;
  }
  list.innerHTML = alerts.map((alert) => `
    <li>
      <strong>${alert.niveau || 'INFO'}</strong> · ${alert.type_alerte || 'ALERTE'}<br>
      <span>${alert.message || ''}</span>
    </li>
  `).join('');
}

function renderReport(report) {
  const el = document.getElementById('reportData');
  if (!report?.summary_text) {
    el.textContent = 'Aucun rapport disponible pour cette station.';
    return;
  }
  el.textContent = report.summary_text;
}

function buildChart(canvasId, labels, values, config) {
  const canvas = document.getElementById(canvasId);
  if(!canvas) return;
  const ctx = canvas.getContext('2d');
  if (state.charts[canvasId]) {
    state.charts[canvasId].destroy();
  }
  state.charts[canvasId] = new Chart(ctx, {
    type: config.type,
    data: {
      labels,
      datasets: [{
        label: config.label,
        data: values,
        borderColor: config.borderColor,
        backgroundColor: config.backgroundColor,
        tension: 0.35,
        fill: config.fill || false,
        pointRadius: 2,
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        x: {
          ticks: { color: '#8ea2c2' },
          grid: { color: 'rgba(255,255,255,0.04)' }
        },
        y: {
          ticks: { color: '#8ea2c2' },
          grid: { color: 'rgba(255,255,255,0.04)' }
        }
      }
    }
  });
}

function renderCharts(hourly) {
  if (!hourly || !hourly.length) {
    renderDailyFallbackCharts();
    return;
  }
  const labels = hourly.map((entry) => {
    const value = entry.date_heure || entry.date || '';
    return new Date(value).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  }).reverse();

  const reversed = [...hourly].reverse();
  buildChart('tempChart', labels, reversed.map((entry) => Number(entry.temperature_2m || 0)), {
    type: 'line',
    label: 'Température',
    borderColor: '#4ba3ff',
    backgroundColor: 'rgba(75,163,255,0.20)',
    fill: true
  });
  buildChart('rainChart', labels, reversed.map((entry) => Number(entry.precipitation || 0)), {
    type: 'bar',
    label: 'Pluie',
    borderColor: '#48d6d2',
    backgroundColor: 'rgba(72,214,210,0.35)'
  });
  buildChart('humidityChart', labels, reversed.map((entry) => Number(entry.relative_humidity_2m || 0)), {
    type: 'line',
    label: 'Humidité',
    borderColor: '#7ce38b',
    backgroundColor: 'rgba(124,227,139,0.18)',
    fill: true
  });
  buildChart('windChart', labels, reversed.map((entry) => Number(entry.wind_speed_10m || 0)), {
    type: 'line',
    label: 'Vent',
    borderColor: '#f4c86b',
    backgroundColor: 'rgba(244,200,107,0.18)',
    fill: true
  });
  buildChart('pressureChart', labels, reversed.map((entry) => Number(entry.surface_pressure || 0)), {
    type: 'line',
    label: 'Pression',
    borderColor: '#a78bfa',
    backgroundColor: 'rgba(167,139,250,0.18)',
    fill: true
  });

  updateMetricCards(hourly);
}

async function renderDailyFallbackCharts() {
  if (!state.activeStationId) return;
  const daily = getResults(await fetchJSON(`/weather-stations/${state.activeStationId}/daily-trend/?days=7`).catch(() => []));
  if (!daily.length) return;

  const rows = daily.slice().reverse();
  const labels = rows.map((entry) => entry.date);
  const temps = rows.map((entry) => Number(entry.temperature_avg || 0));
  const rain = rows.map((entry) => Number(entry.precipitation_sum || 0));
  const humidity = rows.map((entry) => Number(entry.relative_humidity_avg || 0));
  const wind = rows.map((entry) => Number(entry.wind_speed_avg || 0));

  buildChart('tempChart', labels, temps, {
    type: 'line',
    label: 'Température moyenne',
    borderColor: '#4ba3ff',
    backgroundColor: 'rgba(75,163,255,0.20)',
    fill: true
  });
  buildChart('rainChart', labels, rain, {
    type: 'bar',
    label: 'Pluie',
    borderColor: '#48d6d2',
    backgroundColor: 'rgba(72,214,210,0.35)'
  });
  buildChart('humidityChart', labels, humidity, {
    type: 'line',
    label: 'Humidité',
    borderColor: '#7ce38b',
    backgroundColor: 'rgba(124,227,139,0.18)',
    fill: true
  });
  buildChart('windChart', labels, wind, {
    type: 'line',
    label: 'Vent moyen',
    borderColor: '#f4c86b',
    backgroundColor: 'rgba(244,200,107,0.18)',
    fill: true
  });
  buildChart('pressureChart', labels, labels.map(() => null), {
    type: 'line',
    label: 'Pression',
    borderColor: '#a78bfa',
    backgroundColor: 'rgba(167,139,250,0.18)',
    fill: true
  });

  updateMetricCardsFromDaily(rows);
}

async function loadRegionsAndStations() {
  const [regionsPayload, stationsPayload] = await Promise.all([
    fetchJSON('/regions/'),
    fetchJSON('/weather-stations/')
  ]);

  state.regions = getResults(regionsPayload);
  state.stations = getResults(stationsPayload).map((station) => {
    // normalize region to id and keep region_name for display
    const regionId = (typeof station.region === 'object') ? (station.region?.id) : station.region;
    const regionName = (typeof station.region === 'object') ? (station.region?.nom_region) : station.region_name;
    return { ...station, region: regionId, region_name: regionName };
  });

  const regionSelect = document.getElementById('regionSelect');
  const stationSelect = document.getElementById('stationSelect');

  regionSelect.innerHTML = '<option value="">Toutes les régions</option>';
  state.regions.forEach((region) => {
    const option = document.createElement('option');
    option.value = region.id;
    option.textContent = region.nom_region;
    regionSelect.appendChild(option);
  });

  stationSelect.innerHTML = '';
  fillStationSelect();
  clearMarkers();
  state.stations.forEach(addStationMarker);
  fitMapToStations(state.stations);

  if (state.stations.length) {
    state.activeStationId = String(state.stations[0].id);
    stationSelect.value = state.activeStationId;
    state.activeRegionId = state.stations[0].region ? String(state.stations[0].region) : '';
    regionSelect.value = state.activeRegionId;
  }
}

function fillStationSelect() {
  const stationSelect = document.getElementById('stationSelect');
  const filteredStations = state.stations.filter((station) => {
    if (!state.activeRegionId) {
      return true;
    }
    return String(station.region) === String(state.activeRegionId);
  });

  stationSelect.innerHTML = filteredStations.length
    ? filteredStations.map((station) => `<option value="${station.id}">${station.nom_station}</option>`).join('')
    : '<option value="">Aucune station</option>';

  if (filteredStations.length) {
    state.activeStationId = String(filteredStations[0].id);
    stationSelect.value = state.activeStationId;
  } else {
    state.activeStationId = '';
  }
}

async function loadDashboardData() {
  if (!state.activeStationId) {
    renderStationInfo(null, null);
    renderAlerts([]);
    renderReport(null);
    renderCharts([]);
    return;
  }

  const station = state.stations.find((item) => String(item.id) === String(state.activeStationId));
  const region = state.regions.find((item) => String(item.id) === String(state.activeRegionId || station?.region));

  renderStationInfo(station, region);

  const hours = state.activeHours;
  const [current, hourly, report, alerts] = await Promise.all([
    fetchJSON(`/weather-stations/${state.activeStationId}/current/`).catch(() => null),
    fetchJSON(`/weather-stations/${state.activeStationId}/hourly-history/?hours=${hours}`),
    fetchJSON(`/weather-stations/${state.activeStationId}/report-today/`).catch(() => null),
    fetchJSON(`/weather-stations/${state.activeStationId}/active-alerts/`).catch(() => [])
  ]);

  const hourlyResults = getResults(hourly);
  if (hourlyResults.length) {
    renderCharts(hourlyResults);
  } else {
    await renderDailyFallbackCharts();
  }

  if (current && Object.keys(current).length) {
    document.getElementById('metricTemp').textContent = formatNumber(current.temperature_2m);
    document.getElementById('metricRain').textContent = formatNumber(current.precipitation);
    document.getElementById('metricHumidity').textContent = formatNumber(current.relative_humidity_2m);
    document.getElementById('metricWind').textContent = formatNumber(current.wind_speed_10m);
    document.getElementById('metricPressure').textContent = formatNumber(current.surface_pressure, 0);
  }
  renderReport(report);
  renderAlerts(getResults(alerts));
  setLastRefresh();
}

function bindEvents() {
  document.getElementById('regionSelect').addEventListener('change', async (event) => {
    state.activeRegionId = event.target.value;
    fillStationSelect();
    // focus map to region's stations
    const filtered = state.stations.filter((station) => {
      if (!state.activeRegionId) return true;
      return String(station.region) === String(state.activeRegionId);
    });
    if (filtered.length) {
      fitMapToStations(filtered);
    }
    await loadDashboardData();
  });

  document.getElementById('stationSelect').addEventListener('change', async (event) => {
    state.activeStationId = event.target.value;
    // ensure regionSelect reflects selected station's region
    const st = state.stations.find((s) => String(s.id) === String(state.activeStationId));
    if (st && st.region) {
      state.activeRegionId = String(st.region);
      const regionSelect = document.getElementById('regionSelect');
      if (regionSelect) regionSelect.value = state.activeRegionId;
    }
    await loadDashboardData();
  });

  document.getElementById('periodSelect').addEventListener('change', async (event) => {
    state.activeHours = Number(event.target.value);
    await loadDashboardData();
  });

  document.getElementById('refreshButton').addEventListener('click', async () => {
    await loadDashboardData();
  });
}

window.addEventListener('DOMContentLoaded', async () => {
  initMap();
  bindEvents();
  await loadRegionsAndStations();
  await loadDashboardData();
});
