// JS pour la liste et le détail des rapports
(function(){
  const apiReports = '/weather-reports/?ordering=-date';
  const apiRegions = '/regions/with-station/';

  function fetchJSON(url){ return fetch(url).then(r=>r.json()).catch(()=>null); }

  function renderList(reports){
    const ul = document.getElementById('reportsList'); if(!ul) return;
    ul.innerHTML = '';
    if(!Array.isArray(reports) || !reports.length){ ul.innerHTML = '<li>Aucun rapport</li>'; return; }
    reports.forEach(r=>{
      const li = document.createElement('li');
      li.className = 'report-item';
      const a = document.createElement('a'); a.href = `/reports/${r.id}/`; a.textContent = `${r.date} — ${r.station ? r.station.nom_station : 'Station '+(r.station||'')}`;
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

    function load(){
      let url = '/weather-reports/?ordering=-date';
      if(dateInput && dateInput.value) url += `&date=${dateInput.value}`;
      if(regionSelect && regionSelect.value) url += `&station__region=${regionSelect.value}`;
      fetchJSON(url).then(renderList);
    }

    btn?.addEventListener('click', load);
    // initial load
    load();
  }

  function initDetail(){
    // infer id from path
    const parts = window.location.pathname.split('/').filter(Boolean);
    const id = parts[parts.length-1];
    if(!id || isNaN(parseInt(id,10))) return;
    fetchJSON(`/weather-reports/${id}/`).then(r=>{
      if(!r) return;
      document.getElementById('reportDate') && (document.getElementById('reportDate').textContent = r.date);
      document.getElementById('reportStation') && (document.getElementById('reportStation').textContent = r.station ? r.station.nom_station : 'Station');
      document.getElementById('reportSummary') && (document.getElementById('reportSummary').textContent = r.summary_text || '');
      const inds = document.getElementById('reportIndicators');
      if(inds){ inds.innerHTML = `<div class="metric-card"><strong>${r.temperature_avg||'--'}</strong><div>Temp moy</div></div><div class="metric-card"><strong>${r.precipitation_sum||'--'}</strong><div>Pluie</div></div><div class="metric-card"><strong>${r.humidity_avg||'--'}</strong><div>Humidité</div></div><div class="metric-card"><strong>${r.wind_speed_avg||'--'}</strong><div>Vent</div></div>`; }
    });
  }

  document.addEventListener('DOMContentLoaded', ()=>{
    if(document.getElementById('reportsList')) initList();
    if(document.getElementById('reportContent') || window.location.pathname.startsWith('/reports/')) initDetail();
  });
})();
