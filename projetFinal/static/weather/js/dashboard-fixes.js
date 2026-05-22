// Minimal dashboard fixes: map init and wind/pressure charts
(function(){
  const regionsUrl = '/regions/with-station/';
  function fetchJSON(u){ return fetch(u).then(r=>r.json()).catch(()=>null); }

  function initMap(){
    if(typeof L === 'undefined') return;
    const mapEl = document.getElementById('map');
    if(!mapEl) return;

    const populateWhenReady = (map) => {
      const allMarkers = window.dashboardMarkers || L.layerGroup().addTo(map);
      const regionCoords = {};
      fetchJSON(regionsUrl).then(data=>{
        if(!Array.isArray(data)) return;
        data.forEach(r=>{
          const stations = Array.isArray(r.station) ? r.station : (r.station ? [r.station] : []);
          stations.forEach(st=>{
            if(st && st.latitude && st.longitude){
              const lat = parseFloat(st.latitude);
              const lon = parseFloat(st.longitude);
              const marker = L.circleMarker([lat,lon],{radius:8,fillColor:'#4ba3ff',color:'#fff',weight:1,fillOpacity:0.9});
              marker.bindPopup(`<strong>${st.nom_station}</strong><div>${r.nom_region}</div>`);
              marker.on('click', ()=>{
                const sel = document.getElementById('stationSelect');
                if(sel){
                  let opt = Array.from(sel.options).find(o=>String(o.value)===String(st.id));
                  if(!opt){ opt = document.createElement('option'); opt.value = st.id; opt.textContent = st.nom_station || `Station ${st.id}`; sel.appendChild(opt); }
                  sel.value = st.id; sel.dispatchEvent(new Event('change'));
                  const p = document.getElementById('periodSelect'); let hours = 24; if(p){ const pv = parseInt(p.value,10); hours = (pv>48)?168:pv; }
                  try{ renderWindPressure(st.id, hours); }catch(e){ console.debug('renderWindPressure err', e); }
                }
                document.getElementById('refreshButton')?.click();
              });
              marker.addTo(allMarkers);
              if(r.id){ regionCoords[r.id] = regionCoords[r.id] || []; regionCoords[r.id].push([lat,lon]); }
            }
          });
        });
        window.dashboardMarkers = allMarkers;
        window.dashboardRegionCoords = regionCoords;
      }).catch(()=>{
        window.dashboardMarkers = allMarkers;
        window.dashboardRegionCoords = {};
      });

      // focus map when regionSelect changes
      document.addEventListener('change', (e)=>{
        if(!e.target || e.target.id !== 'regionSelect') return;
        const regionId = e.target.value;
        if(!regionId){
          const all = [];
          Object.values(window.dashboardRegionCoords || {}).forEach(arr=> arr.forEach(p=> all.push(p)));
          if(all.length){ const bounds = L.latLngBounds(all); map.fitBounds(bounds.pad ? bounds.pad(0.2) : bounds, {padding:[50,50]}); }
          else map.setView([-18.9,47.5],5);
          return;
        }
        const coords = (window.dashboardRegionCoords && window.dashboardRegionCoords[regionId]) || [];
        if(coords.length===1){ map.setView(coords[0], 10); }
        else if(coords.length>1){ const bounds = L.latLngBounds(coords); map.fitBounds(bounds, {padding:[40,40]}); }
      });

      // when stationSelect changes, render wind/pressure automatically
      document.addEventListener('change', (e)=>{
        if(!e.target || e.target.id !== 'stationSelect') return;
        const sid = e.target.value; if(!sid) return;
        const p = document.getElementById('periodSelect'); let hours = 24; if(p){ const pv = parseInt(p.value,10); hours = (pv>48)?168:pv; }
        renderWindPressure(sid, hours);
      });
    };

    // If another script created the map, reuse it
    if(window.dashboardMap){ populateWhenReady(window.dashboardMap); return; }

    // wait for other scripts to initialize map (short timeout), otherwise create our own
    let attempts = 0;
    const waiter = setInterval(()=>{
      attempts += 1;
      if(window.dashboardMap){ clearInterval(waiter); populateWhenReady(window.dashboardMap); return; }
      if(attempts>20){ clearInterval(waiter);
        const map = L.map(mapEl).setView([-18.9,47.5], 5);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom: 18}).addTo(map);
        window.dashboardMap = map;
        populateWhenReady(map);
      }
    },100);
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
