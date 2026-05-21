// Minimal dashboard fixes: map init and wind/pressure charts
(function(){
  const regionsUrl = '/regions/with-station/';
  function fetchJSON(u){ return fetch(u).then(r=>r.json()).catch(()=>null); }

  function initMap(){
    if(typeof L === 'undefined') return;
    const mapEl = document.getElementById('map');
    if(!mapEl) return;
    const map = L.map(mapEl).setView([-18.9,47.5], 5);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom: 18}).addTo(map);
    fetchJSON(regionsUrl).then(data=>{
      if(!Array.isArray(data)) return;
      data.forEach(r=>{
        if(r.station && r.station.latitude && r.station.longitude){
          const lat = parseFloat(r.station.latitude);
          const lon = parseFloat(r.station.longitude);
          const marker = L.circleMarker([lat,lon],{radius:8,fillColor:'#4ba3ff',color:'#fff',weight:1,fillOpacity:0.9}).addTo(map);
          marker.bindPopup(`<strong>${r.station.nom_station}</strong><div>${r.nom_region}</div>`);
          marker.on('click', ()=>{
            const sel = document.getElementById('stationSelect');
            if(sel){ sel.value = r.station.id; sel.dispatchEvent(new Event('change')); }
            document.getElementById('refreshButton')?.click();
          });
        }
      });
    });
  }

  function renderWindPressure(stationId, hours){
    if(!stationId) return;
    fetchJSON(`/weather-stations/${stationId}/hourly-history/?hours=${hours}`).then(data=>{
      if(!Array.isArray(data)) return;
      const rows = data.slice().reverse();
      const labels = rows.map(r=>r.date_heure.replace('T',' '));
      const wind = rows.map(r=>r.wind_speed_10m || r.wind_speed || null);
      const pres = rows.map(r=>r.surface_pressure || null);

      const wctx = document.getElementById('windChart');
      if(wctx){ if(wctx._chart) wctx._chart.destroy(); wctx._chart = new Chart(wctx,{type:'line',data:{labels,datasets:[{label:'Vent (km/h)',data:wind,borderColor:'#9f7aea',tension:0.2}]},options:{responsive:true}}); }

      const pctx = document.getElementById('pressureChart');
      if(pctx){ if(pctx._chart) pctx._chart.destroy(); pctx._chart = new Chart(pctx,{type:'line',data:{labels,datasets:[{label:'Pression (hPa)',data:pres,borderColor:'#f4c86b',tension:0.2}]},options:{responsive:true}}); }
    }).catch(err=>console.debug('wind/press load',err));
  }

  document.addEventListener('DOMContentLoaded', ()=>{
    initMap();
    const global = document.getElementById('refreshButton');
    if(global){ global.addEventListener('click', ()=>{
      const s = document.getElementById('stationSelect'); if(!s||!s.value) return;
      const p = document.getElementById('periodSelect'); let hours = 24; if(p){ const pv = parseInt(p.value,10); hours = (pv>48)?168:pv; }
      renderWindPressure(s.value, hours);
    });
    }
  });
})();
