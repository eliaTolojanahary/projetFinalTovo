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
  });
})();
