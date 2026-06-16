// visualization.js — Rendu des graphiques pour les pages Historique et Tendances.
// L'état (station, period, days) est transmis par le dashboard en query params d'URL.
// Aucun postMessage, aucun __PARENT_STATE, aucune gestion de sélecteurs internes.

(function () {
  const API = '/weather-stations/';

  // ── Lecture des params ─────────────────────────────────────────────────────
  function qs(name) {
    return new URLSearchParams(window.location.search).get(name);
  }

  const stationId = qs('station');
  const hours     = parseInt(qs('period') || '24', 10);
  const days      = parseInt(qs('days')   || '7',  10);

  // ── Fetch ──────────────────────────────────────────────────────────────────
  function fetchJSON(url) {
    return fetch(url).then(r => {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    });
  }

  // ── Gestion des instances Chart.js ────────────────────────────────────────
  const _charts = {};

  function renderChart(id, config) {
    const el = document.getElementById(id);
    if (!el) return;
    if (_charts[id]) _charts[id].destroy();
    _charts[id] = new Chart(el, config);
  }

  function lineConfig(label, data, color) {
    return {
      type: 'line',
      data: { labels: data.labels, datasets: [{ label, data: data.values, borderColor: color, tension: 0.2, pointRadius: 2 }] },
      options: { responsive: true, plugins: { legend: { display: false } } }
    };
  }

  function barConfig(label, data, color) {
    return {
      type: 'bar',
      data: { labels: data.labels, datasets: [{ label, data: data.values, backgroundColor: color }] },
      options: { responsive: true, plugins: { legend: { display: false } } }
    };
  }

  // ── Page Historique ───────────────────────────────────────────────────────

  function renderHistorique(sid, h) {
    fetchJSON(`${API}${sid}/hourly-history/?hours=${h}`)
      .then(data => {
        const rows = Array.isArray(data) && data.length ? data.slice().reverse() : null;
        if (!rows) { renderHistoriqueFallback(sid); return; }

        const labels = rows.map(r => r.date_heure.replace('T', ' '));

        renderChart('tempChart',     lineConfig('Température (°C)',   { labels, values: rows.map(r => r.temperature_2m)              }, '#ff7f50'));
        renderChart('precipChart',   barConfig( 'Précipitation (mm)', { labels, values: rows.map(r => r.precipitation || 0)          }, '#4da6ff'));
        renderChart('humidityChart', lineConfig('Humidité (%)',        { labels, values: rows.map(r => r.relative_humidity_2m || r.humidity) }, '#00cc99'));
      })
      .catch(() => renderHistoriqueFallback(sid));
  }

  function renderHistoriqueFallback(sid) {
    fetchJSON(`${API}${sid}/daily-trend/?days=7`)
      .then(data => {
        if (!Array.isArray(data) || !data.length) return;
        const rows   = data.slice().reverse();
        const labels = rows.map(r => r.date);

        renderChart('tempChart',     lineConfig('Température moy.',   { labels, values: rows.map(r => r.temperature_avg)            }, '#ff7f50'));
        renderChart('precipChart',   barConfig( 'Précipitation (mm)', { labels, values: rows.map(r => r.precipitation_sum || 0)     }, '#4da6ff'));
        renderChart('humidityChart', lineConfig('Humidité (%)',        { labels, values: rows.map(r => r.relative_humidity_avg || null) }, '#00cc99'));
      });
  }

  // ── Page Tendances ────────────────────────────────────────────────────────

  function renderTendances(sid, d) {
    fetchJSON(`${API}${sid}/daily-trend/?days=${d}`)
      .then(data => {
        if (!Array.isArray(data) || !data.length) return;
        const rows   = data.slice().reverse();
        const labels = rows.map(r => r.date);
        const tmin   = rows.map(r => r.temperature_min);
        const tavg   = rows.map(r => r.temperature_avg);
        const tmax   = rows.map(r => r.temperature_max);
        const precip = rows.map(r => r.precipitation_sum || 0);
        const humid  = rows.map(r => r.relative_humidity_avg || null);

        renderChart('dailyTempChart', {
          type: 'line',
          data: {
            labels,
            datasets: [
              { label: 'Min', data: tmin, borderColor: '#3b82f6', tension: 0.2 },
              { label: 'Moy', data: tavg, borderColor: '#ffb020', tension: 0.2 },
              { label: 'Max', data: tmax, borderColor: '#ef4444', tension: 0.2 }
            ]
          },
          options: { responsive: true }
        });

        renderChart('dailyPrecipChart',   barConfig( 'Précipitation (mm)', { labels, values: precip }, '#4da6ff'));
        renderChart('dailyHumidityChart', lineConfig('Humidité (%)',        { labels, values: humid  }, '#00cc99'));
      });
  }

  // ── Init ──────────────────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', () => {
    if (!stationId) {
      console.warn('[visualization] Aucun stationId dans les params URL.');
      return;
    }

    if (document.getElementById('dailyTempChart')) {
      renderTendances(stationId, days);
    } else {
      renderHistorique(stationId, hours);
    }
  });
})();