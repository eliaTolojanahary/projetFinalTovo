// Shared visualization JS for historique and tendances pages
(function(){
  const api = {
    regions: '/regions/with-station/',
    stations: '/weather-stations/',
  };

  function readStateFromQuery(){
    const params = new URLSearchParams(window.location.search);
    const regionId = params.get('region');
    const stationId = params.get('station');
    const period = params.get('period');
    const hours = params.get('hours');
    const days = params.get('days');
    const has = regionId || stationId || period || hours || days;
    return has ? { regionId, stationId, period, hours, days } : null;
  }

  const pageState = {
    regionId: '',
    stationId: '',
    period: '',
    hours: '24',
    days: '7'
  };

  const initialState = (window.__PARENT_STATE && Object.keys(window.__PARENT_STATE).length)
    ? window.__PARENT_STATE
    : (readStateFromQuery() || {});

  Object.assign(pageState, initialState);

  function setPageState(nextState){
    if(!nextState) return;
    Object.assign(pageState, nextState);
  }

  function fetchJSON(url){
    return fetch(url).then(r=>r.json());
  }

  function populateRegions(){
    const rselect = document.getElementById('regionSelect');
    const sselect = document.getElementById('stationSelect');
    if(!rselect || !sselect) return Promise.resolve();
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
        if(sselect.options.length){
          sselect.selectedIndex = 0;
          sselect.dispatchEvent(new Event('change', { bubbles: true }));
        }
      });
      if(pageState.regionId){
        rselect.value = String(pageState.regionId);
      }
      if(pageState.stationId){
        sselect.value = String(pageState.stationId);
      }

      // trigger initial change and initial render
      if(rselect.value){
        rselect.dispatchEvent(new Event('change', { bubbles: true }));
      }
      const firstStation = sselect.value || pageState.stationId;
      if(firstStation){
        renderForSelectedPage(firstStation);
      }
    }).catch(err=>{console.error('Failed load regions', err)});
  }

  function makeChart(ctx, config){
    return new Chart(ctx, config);
  }

  function getSelectedHours(){
    if(pageState.hours) return pageState.hours;
    const p = document.getElementById('periodSelect');
    if(p){
      const pv = parseInt(p.value,10);
      if(!Number.isNaN(pv)) return (pv>48)?168:pv;
    }
    const hsel = document.getElementById('hoursSelect');
    if(hsel && hsel.value) return hsel.value;
    return 24;
  }

  function getSelectedDays(){
    if(pageState.days) return pageState.days;
    const dsel = document.getElementById('daysSelect');
    if(dsel && dsel.value) return dsel.value;
    return 7;
  }

  function renderForSelectedPage(stationId){
    if(!stationId) return;
    pageState.stationId = String(stationId);
    loadOverview(stationId);
    if(document.getElementById('hist_tempChart') || document.getElementById('tempChart')){
      renderHourlyCharts(stationId, getSelectedHours());
    }
    if(document.getElementById('dailyTempChart')){
      renderDailyCharts(stationId, getSelectedDays());
    }
  }

  function renderHourlyCharts(stationId, hours){
    const url = `${api.stations}${stationId}/hourly-history/?hours=${hours}`;
    fetchJSON(url).then(data=>{
      if(!Array.isArray(data) || data.length === 0){
        // fallback to daily data when hourly history is empty
        renderDailyFallbackCharts(stationId);
        return;
      }
      // data are ordered desc by date_heure in backend; reverse for chronological
      const rows = data.slice().reverse();
      const labels = rows.map(r=>r.date_heure.replace('T',' '));
      const temps = rows.map(r=>r.temperature_2m);
      const humid = rows.map(r=>r.relative_humidity_2m || r.humidity);
      const precip = rows.map(r=>r.precipitation || r.precipitation_1h || 0);

      // Temperature chart (historique)
      const tctx = document.getElementById('hist_tempChart') || document.getElementById('tempChart');
      if(tctx){
        if(tctx._chart) tctx._chart.destroy();
        tctx._chart = makeChart(tctx, {
          type: 'line',
          data: {labels, datasets:[{label:'Température',data:temps,borderColor:'#ff7f50',tension:0.2}]},
          options: {responsive:true}
        });
      }

      // Precip chart (historique)
      const pctx = document.getElementById('hist_precipChart') || document.getElementById('precipChart') || document.getElementById('rainChart');
      if(pctx){
        if(pctx._chart) pctx._chart.destroy();
        pctx._chart = makeChart(pctx, {
          type: 'bar',
          data: {labels, datasets:[{label:'Précipitation (mm)',data:precip,backgroundColor:'#4da6ff'}]},
          options: {responsive:true}
        });
      }

      // Humidity chart (historique)
      const hctx = document.getElementById('hist_humidityChart') || document.getElementById('humidityChart');
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

  function renderDailyFallbackCharts(stationId){
    const url = `${api.stations}${stationId}/daily-trend/?days=7`;
    fetchJSON(url).then(data=>{
      if(!Array.isArray(data) || !data.length) return;
      const rows = data.slice().reverse();
      const labels = rows.map(r=>r.date);
      const temps = rows.map(r=>r.temperature_avg);
      const humid = rows.map(r=>r.relative_humidity_avg || r.humidity_avg || null);
      const precip = rows.map(r=>r.precipitation_sum || 0);

      const tctx = document.getElementById('hist_tempChart') || document.getElementById('tempChart');
      if(tctx){
        if(tctx._chart) tctx._chart.destroy();
        tctx._chart = makeChart(tctx, {
          type: 'line',
          data: {labels, datasets:[{label:'Température moyenne',data:temps,borderColor:'#ff7f50',tension:0.2}]},
          options: {responsive:true}
        });
      }

      const pctx = document.getElementById('hist_precipChart') || document.getElementById('precipChart') || document.getElementById('rainChart');
      if(pctx){
        if(pctx._chart) pctx._chart.destroy();
        pctx._chart = makeChart(pctx, {
          type: 'bar',
          data: {labels, datasets:[{label:'Précipitation (mm)',data:precip,backgroundColor:'#4da6ff'}]},
          options: {responsive:true}
        });
      }

      const hctx = document.getElementById('hist_humidityChart') || document.getElementById('humidityChart');
      if(hctx){
        if(hctx._chart) hctx._chart.destroy();
        hctx._chart = makeChart(hctx, {
          type: 'line',
          data: {labels, datasets:[{label:'Humidité',data:humid,borderColor:'#00cc99',tension:0.2}]},
          options: {responsive:true}
        });
      }
    }).catch(err=>console.error('daily fallback load', err));
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
      const humid = rows.map(r=>r.relative_humidity_avg || r.humidity_avg || null);

      const ttctx = document.getElementById('dailyTempChart');
      if(ttctx){ if(ttctx._chart) ttctx._chart.destroy(); ttctx._chart = makeChart(ttctx, {type:'line',data:{labels,datasets:[{label:'Min',data:tmin,borderColor:'#3b82f6'},{label:'Moy',data:tavg,borderColor:'#ffb020'},{label:'Max',data:tmax,borderColor:'#ef4444'}]},options:{responsive:true}}); }

      const pdctx = document.getElementById('dailyPrecipChart');
      if(pdctx){ if(pdctx._chart) pdctx._chart.destroy(); pdctx._chart = makeChart(pdctx, {type:'bar',data:{labels,datasets:[{label:'Précipitation',data:precip,backgroundColor:'#4da6ff'}]},options:{responsive:true}}); }

      const hdctx = document.getElementById('dailyHumidityChart');
      if(hdctx){ if(hdctx._chart) hdctx._chart.destroy(); hdctx._chart = makeChart(hdctx, {type:'line',data:{labels,datasets:[{label:'Humidité',data:humid,borderColor:'#00cc99'}]},options:{responsive:true}}); }
    }).catch(err=>console.error('daily load',err));
  }

  function loadOverview(stationId){
    if(!stationId) return;
    // current
    fetchJSON(`${api.stations}${stationId}/current`).then(current=>{
      if(current){
        const t = current.temperature_2m || current.temperature_2m;
        const h = current.relative_humidity_2m || current.humidity || '';
        const p = current.precipitation || current.rain || 0;
        const w = current.wind_speed_10m || '';
        const pres = current.surface_pressure || '';
          const setText = (id, v)=>{ const el = document.getElementById(id); if(!el) return; el.textContent = (v===null||v===undefined)? '--' : String(v); };
          setText('metricTemp', t);
          setText('metricHumidity', h);
          setText('metricRain', p);
          setText('metricWind', w);
          setText('metricPressure', pres);
        // station short info
        const si = document.getElementById('stationInfo');
        if(si){ si.innerHTML = `<div class="station-pill">Station ID: ${stationId}</div>`; }
      }
    }).catch(err=>{console.debug('no current',err)});

    // report
    fetchJSON(`${api.stations}${stationId}/report-today/`).then(report=>{
      const rd = document.getElementById('reportData');
      if(rd){ rd.textContent = report ? (report.summary_text || 'Pas de rapport') : 'Pas de rapport'; }
    }).catch(err=>{ const rd = document.getElementById('reportData'); if(rd) rd.textContent = 'Pas de rapport'; });

    // alerts
    fetchJSON(`${api.stations}${stationId}/active-alerts/`).then(alerts=>{
      const ul = document.getElementById('alertsList');
      if(!ul) return;
      ul.innerHTML = '';
      if(Array.isArray(alerts) && alerts.length){
        alerts.forEach(a=>{
          const li = document.createElement('li'); li.textContent = `${a.niveau || ''} - ${a.message || a.type_alerte || 'Alerte'}`; ul.appendChild(li);
        });
      } else {
        ul.innerHTML = '<li>Aucune alerte</li>';
      }
    }).catch(err=>{ console.debug('alerts err',err); });
  }

  function init(){
    populateRegions();

    // If the page has no filters, render immediately from the received request state.
    if(!document.getElementById('stationSelect')){
      const bootstrap = async ()=>{
        let stationId = pageState.stationId;
        if(!stationId){
          const stations = await fetchJSON(api.stations).catch(()=>[]);
          const firstStation = Array.isArray(stations) ? stations[0] : null;
          stationId = firstStation?.id ? String(firstStation.id) : '';
        }
        if(stationId){
          renderForSelectedPage(stationId);
        }
      };
      bootstrap();
    }

    const refresh = document.getElementById('refreshBtn') || document.getElementById('refreshButton');
    if(refresh){
      refresh.addEventListener('click', ()=>{
      const s = document.getElementById('stationSelect');
      if(!s || !s.value) return;
      const stationId = s.value;
      // decide page type: historique vs tendances
      if(document.getElementById('hist_tempChart') || document.getElementById('tempChart')){
        renderHourlyCharts(stationId, getSelectedHours());
      }
      if(document.getElementById('dailyTempChart')){
        renderDailyCharts(stationId, getSelectedDays());
      }
      });
    }

    // auto-load daily charts on the Tendances page
    if(document.getElementById('dailyTempChart')){
      const s = document.getElementById('stationSelect');
      if(s && s.value){
        renderDailyCharts(s.value, getSelectedDays());
      }
    }

    document.addEventListener('change', (e)=>{
      if(!e.target) return;
      if(e.target.id === 'stationSelect'){
        if(e.target.value) renderForSelectedPage(e.target.value);
      }
      if(e.target.id === 'hoursSelect' || e.target.id === 'daysSelect' || e.target.id === 'periodSelect'){
        const s = document.getElementById('stationSelect');
        if(s && s.value) renderForSelectedPage(s.value);
      }
    });
  }

  // allow parent dashboard to control this page via postMessage
  let _parentPendingState = null;
  function applyParentState(state){
    if(!state) return;
    setPageState(state);
    const rselect = document.getElementById('regionSelect');
    const sselect = document.getElementById('stationSelect');
    const hoursSelect = document.getElementById('hoursSelect');
    const daysSelect = document.getElementById('daysSelect');
    const periodSelect = document.getElementById('periodSelect');

    // Pages without controls should render immediately from the received request state.
    if(!rselect && !sselect){
      const stationId = state.stationId || pageState.stationId;
      if(stationId){
        renderForSelectedPage(stationId);
      }
      return;
    }

    // if selects are not yet populated, store pending and return
    if(rselect && rselect.options.length === 0){
      _parentPendingState = state;
      return;
    }

    if(state.regionId && rselect){ rselect.value = state.regionId; rselect.dispatchEvent(new Event('change', {bubbles:true})); }
    if(state.stationId && sselect){
      // station options may be populated after region change; try set, else defer
      const opt = Array.from(sselect.options).find(o => String(o.value) === String(state.stationId));
      if(opt){ sselect.value = state.stationId; sselect.dispatchEvent(new Event('change', {bubbles:true})); }
      else {
        // wait a short time for stations to populate
        setTimeout(()=>{ const opt2 = Array.from(sselect.options).find(o => String(o.value) === String(state.stationId)); if(opt2){ sselect.value = state.stationId; sselect.dispatchEvent(new Event('change', {bubbles:true})); if(sselect.value) renderForSelectedPage(sselect.value); } }, 300);
      }
    }

    if(periodSelect && state.period){ periodSelect.value = state.period; }
    if(hoursSelect && state.hours){ hoursSelect.value = state.hours; }
    if(daysSelect && state.days){ daysSelect.value = state.days; }

    // trigger rendering based on station
    if(state.stationId){ renderForSelectedPage(state.stationId); }
  }

  window.addEventListener('message', (ev)=>{
    try{
      if(ev.origin !== window.location.origin) return;
    }catch(e){ /* ignore */ }
    const msg = ev.data || {};
    if(msg && msg.type === 'parentState'){
      applyParentState(msg.state);
    }
  });

  // notify parent we're ready to receive state
  function notifyParentReady(){
    if(window.parent && window.parent !== window){
      try{ window.parent.postMessage({type:'childReady'}, window.location.origin); }catch(e){}
    }
  }

  // when regions are populated, apply any pending parent state
  const _origPopulateRegions = populateRegions;
  populateRegions = function(){
    _origPopulateRegions();
    // small timeout to allow population to finish
    setTimeout(()=>{ if(_parentPendingState){ applyParentState(_parentPendingState); _parentPendingState = null; } }, 400);
  };

  // also read state from query params (when dashboard passes via ?station=...)
  document.addEventListener('DOMContentLoaded', ()=>{
    // priority: injected parent state (srcdoc) -> query params -> none
    const injected = window.__PARENT_STATE || null;
    const qstate = readStateFromQuery();
    if(injected && Object.keys(injected).length){ _parentPendingState = injected; }
    else if(qstate){ _parentPendingState = qstate; }
    init(); notifyParentReady();
  });
})();
