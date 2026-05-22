// JS pour la liste et le détail des rapports
(function(){
  const apiReportsBase = '/weather-reports/';
  const apiRegions = '/regions/with-station/';
  const apiStations = '/weather-stations/';

  function fetchJSON(url){ return fetch(url).then(r=>{ if(!r.ok) return null; return r.json(); }).catch(()=>null); }

  function normalizeResults(resp){
    if(!resp) return [];
    if(Array.isArray(resp)) return resp;
    if(resp.results) return resp.results;
    return [];
  }

  async function loadStationsMap(){
    const map = {};
    // try to grab all stations (page size large)
    const res = await fetchJSON(apiStations+'?page_size=200');
    const list = normalizeResults(res);
    list.forEach(s=>{ map[s.id] = s.nom_station; });
    return map;
  }

  async function renderList(resp){
    const reports = normalizeResults(resp);
    const ul = document.getElementById('reportsList'); if(!ul) return;
    ul.innerHTML = '';
    if(!reports.length){ ul.innerHTML = '<li>Aucun rapport</li>'; return; }
    const stationsMap = await loadStationsMap();
    reports.forEach(r=>{
      const li = document.createElement('li'); li.className='report-item';
      const a = document.createElement('a'); a.href = `/reports/${r.id}/`; 
      const stationName = (r.station && typeof r.station === 'object') ? (r.station.nom_station || '') : (stationsMap[r.station] || `Station ${r.station || ''}`);
      a.textContent = `${r.date} — ${stationName}`;
      const small = document.createElement('div'); small.className='report-meta'; small.textContent = `Temp moy: ${r.temperature_avg||'--'} °C • Pluie: ${r.precipitation_sum||'--'} mm`;
      li.appendChild(a); li.appendChild(small); ul.appendChild(li);
    });
  }

  function initList(){
    const btn = document.getElementById('filterBtn');
    const dateInput = document.getElementById('filterDate');
    const regionSelect = document.getElementById('filterRegion');
    // load regions
    fetchJSON(apiRegions).then(regs=>{
      if(Array.isArray(regs)){
        regionSelect.innerHTML = '<option value="">Toutes</option>';
        regs.forEach(r=>{ const o=document.createElement('option'); o.value=r.id; o.textContent=r.nom_region; regionSelect.appendChild(o); });
      }
    });

    async function load(){
      let url = apiReportsBase + '?ordering=-date';
      if(dateInput && dateInput.value) url += `&date=${dateInput.value}`;
      if(regionSelect && regionSelect.value) url += `&station__region=${regionSelect.value}`;
      const resp = await fetchJSON(url);
      renderList(resp);
    }

    btn?.addEventListener('click', load);
    // initial load
    load();
  }

  async function initDetail(){
    // infer id from path
    const parts = window.location.pathname.split('/').filter(Boolean);
    const id = parts[parts.length-1];
    if(!id || isNaN(parseInt(id,10))) return;
    const r = await fetchJSON(`/weather-reports/${id}/`);
    if(!r) return;
    document.getElementById('reportDate') && (document.getElementById('reportDate').textContent = r.date);
    const stationEl = document.getElementById('reportStation');
    if(stationEl){
      if(r.station && typeof r.station === 'object' && r.station.nom_station) stationEl.textContent = r.station.nom_station;
      else if(r.station) {
        const s = await fetchJSON(`/weather-stations/${r.station}/`);
        stationEl.textContent = s ? s.nom_station : `Station ${r.station}`;
      }
    }
    document.getElementById('reportSummary') && (document.getElementById('reportSummary').textContent = r.summary_text || '');
    const inds = document.getElementById('reportIndicators');
    if(inds){ inds.innerHTML = `<div class="metric-card"><strong>${r.temperature_avg||'--'}</strong><div>Temp moy</div></div><div class="metric-card"><strong>${r.precipitation_sum||'--'}</strong><div>Pluie</div></div><div class="metric-card"><strong>${r.humidity_avg||'--'}</strong><div>Humidité</div></div><div class="metric-card"><strong>${r.wind_speed_avg||'--'}</strong><div>Vent</div></div>`; }
  }

  document.addEventListener('DOMContentLoaded', ()=>{
    if(document.getElementById('reportsList')) initList();
    if(window.location.pathname.startsWith('/reports/')) initDetail();
    // Dashboard integration: list and highlight
    if(document.getElementById('dashboardReportsList') || document.getElementById('highlightContent')){
      initDashboardIntegration();
    }
  });

  // --- Dashboard integration functions ---
  async function initDashboardIntegration(){
    const listEl = document.getElementById('dashboardReportsList');
    const highlightTitle = document.getElementById('highlightTitle');
    const highlightSummary = document.getElementById('highlightSummary');
    const highlightIndicators = document.getElementById('highlightIndicators');

    async function loadForFilters(){
      const stationSelect = document.getElementById('stationSelect');
      const regionSelect = document.getElementById('regionSelect');
      const periodSelect = document.getElementById('periodSelect');
      let url = apiReportsBase + '?ordering=-date&page_size=20';
      if(stationSelect && stationSelect.value) url += `&station=${stationSelect.value}`;
      else if(regionSelect && regionSelect.value) url += `&station__region=${regionSelect.value}`;
      // optionally filter by date derived from period (take latest date)
      const resp = await fetchJSON(url);
      const reports = normalizeResults(resp);
      // populate list
      if(listEl){ listEl.innerHTML = ''; if(!reports.length) listEl.innerHTML = '<li>Aucun rapport</li>'; }
      reports.forEach(r=>{
        if(listEl){ const li = document.createElement('li'); li.className='report-item'; li.textContent = `${r.date} — ${r.station && r.station.nom_station ? r.station.nom_station : ('Station '+(r.station||''))}`; li.dataset.reportId = r.id; li.style.cursor='pointer'; li.addEventListener('click', ()=>{ highlightReport(r); }); listEl.appendChild(li); }
      });
      // auto-highlight first
      if(reports.length) highlightReport(reports[0]);
      else highlightReport(null);
    }

    function highlightReport(r){
      if(!r){ if(highlightTitle) highlightTitle.textContent = 'Aucun rapport disponible'; if(highlightSummary) highlightSummary.textContent = ''; if(highlightIndicators) highlightIndicators.innerHTML=''; return; }
      if(highlightTitle) highlightTitle.textContent = `${r.date} — ${r.station && r.station.nom_station ? r.station.nom_station : ('Station '+(r.station||''))}`;
      if(highlightSummary) highlightSummary.textContent = r.summary_text || '';
      if(highlightIndicators){ highlightIndicators.innerHTML = `<div class="metric-card"><strong>${r.temperature_avg||'--'}</strong><div>Temp moy</div></div><div class="metric-card"><strong>${r.precipitation_sum||'--'}</strong><div>Pluie</div></div><div class="metric-card"><strong>${r.humidity_avg||'--'}</strong><div>Humidité</div></div><div class="metric-card"><strong>${r.wind_speed_avg||'--'}</strong><div>Vent</div></div>`; }
    }

    // attach listeners to filters
    document.getElementById('regionSelect')?.addEventListener('change', loadForFilters);
    document.getElementById('stationSelect')?.addEventListener('change', loadForFilters);
    document.getElementById('periodSelect')?.addEventListener('change', loadForFilters);
    document.getElementById('refreshButton')?.addEventListener('click', loadForFilters);

    // initial load
    loadForFilters();
  }
})();
