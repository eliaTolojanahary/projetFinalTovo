// Shared visualization JS for historique and tendances pages
(function(){
  const api = {
    regions: '/regions/with-station/',
    stations: '/weather-stations/',
  };

  function fetchJSON(url){
    return fetch(url).then(r=>r.json());
  }

  function populateRegions(){
    const rselect = document.getElementById('regionSelect');
    const sselect = document.getElementById('stationSelect');
    if(!rselect) return;
    fetchJSON(api.regions).then(data=>{
      rselect.innerHTML = '';
      data.forEach(r=>{
        const opt = document.createElement('option');
        opt.value = r.id;
        opt.textContent = r.nom_region;
        rselect.appendChild(opt);
      });
      // when region changes, populate stations
      rselect.addEventListener('change', ()=>{
        const regionId = rselect.value;
        sselect.innerHTML = '';
        const region = data.find(x=>String(x.id)===String(regionId));
        if(region && region.station){
          const st = region.station;
          const opt = document.createElement('option');
          opt.value = st.id;
          opt.textContent = st.nom_station;
          sselect.appendChild(opt);
        }
      });
      // trigger initial change
      rselect.dispatchEvent(new Event('change'));
    }).catch(err=>{console.error('Failed load regions', err)});
  }

  function makeChart(ctx, config){
    return new Chart(ctx, config);
  }

  function renderHourlyCharts(stationId, hours){
    const url = `${api.stations}${stationId}/hourly-history/?hours=${hours}`;
    fetchJSON(url).then(data=>{
      if(!Array.isArray(data)) return;
      // data are ordered desc by date_heure in backend; reverse for chronological
      const rows = data.slice().reverse();
      const labels = rows.map(r=>r.date_heure.replace('T',' '));
      const temps = rows.map(r=>r.temperature_2m);
      const humid = rows.map(r=>r.relative_humidity_2m || r.humidity);
      const precip = rows.map(r=>r.precipitation || r.precipitation_1h || 0);

      // Temperature chart
      const tctx = document.getElementById('tempChart');
      if(tctx){
        if(tctx._chart) tctx._chart.destroy();
        tctx._chart = makeChart(tctx, {
          type: 'line',
          data: {labels, datasets:[{label:'Température',data:temps,borderColor:'#ff7f50',tension:0.2}]},
          options: {responsive:true}
        });
      }

      // Precip chart
      const pctx = document.getElementById('precipChart');
      if(pctx){
        if(pctx._chart) pctx._chart.destroy();
        pctx._chart = makeChart(pctx, {
          type: 'bar',
          data: {labels, datasets:[{label:'Précipitation (mm)',data:precip,backgroundColor:'#4da6ff'}]},
          options: {responsive:true}
        });
      }

      // Humidity chart
      const hctx = document.getElementById('humidityChart');
      if(hctx){
        if(hctx._chart) hctx._chart.destroy();
        hctx._chart = makeChart(hctx, {
          type: 'line',
          data: {labels, datasets:[{label:'Humidité',data:humid,borderColor:'#00cc99',tension:0.2}]},
          options: {responsive:true}
        });
      }
    }).catch(err=>console.error('hourly load',err));
  }

  function renderDailyCharts(stationId, days){
    const url = `${api.stations}${stationId}/daily-trend/?days=${days}`;
    fetchJSON(url).then(data=>{
      if(!Array.isArray(data)) return;
      const rows = data.slice().reverse();
      const labels = rows.map(r=>r.date);
      const tmin = rows.map(r=>r.temperature_min);
      const tavg = rows.map(r=>r.temperature_avg);
      const tmax = rows.map(r=>r.temperature_max);
      const precip = rows.map(r=>r.precipitation_sum || 0);
      const humid = rows.map(r=>r.humidity_avg || null);

      const ttctx = document.getElementById('dailyTempChart');
      if(ttctx){ if(ttctx._chart) ttctx._chart.destroy(); ttctx._chart = makeChart(ttctx, {type:'line',data:{labels,datasets:[{label:'Min',data:tmin,borderColor:'#3b82f6'},{label:'Moy',data:tavg,borderColor:'#ffb020'},{label:'Max',data:tmax,borderColor:'#ef4444'}]},options:{responsive:true}}); }

      const pdctx = document.getElementById('dailyPrecipChart');
      if(pdctx){ if(pdctx._chart) pdctx._chart.destroy(); pdctx._chart = makeChart(pdctx, {type:'bar',data:{labels,datasets:[{label:'Précipitation',data:precip,backgroundColor:'#4da6ff'}]},options:{responsive:true}}); }

      const hdctx = document.getElementById('dailyHumidityChart');
      if(hdctx){ if(hdctx._chart) hdctx._chart.destroy(); hdctx._chart = makeChart(hdctx, {type:'line',data:{labels,datasets:[{label:'Humidité',data:humid,borderColor:'#00cc99'}]},options:{responsive:true}}); }
    }).catch(err=>console.error('daily load',err));
  }

  function init(){
    populateRegions();
    const refresh = document.getElementById('refreshBtn');
    if(!refresh) return;
    refresh.addEventListener('click', ()=>{
      const s = document.getElementById('stationSelect');
      if(!s || !s.value) return alert('Sélectionnez une station');
      const stationId = s.value;
      // decide page type
      if(document.getElementById('tempChart')){
        const hours = document.getElementById('hoursSelect').value || 24;
        renderHourlyCharts(stationId, hours);
      } else if(document.getElementById('dailyTempChart')){
        const days = document.getElementById('daysSelect').value || 7;
        renderDailyCharts(stationId, days);
      }
    });
  }

  document.addEventListener('DOMContentLoaded', init);
})();
