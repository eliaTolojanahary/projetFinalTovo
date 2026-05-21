async function fetchJSON(path){
  const res = await fetch(path);
  if(!res.ok) throw new Error(await res.text());
  return res.json();
}

let map, markers = {};

function initMap(){
  map = L.map('map').setView([-18.8792, 47.5079], 5);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
  }).addTo(map);
}

function addStationMarker(station){
  const key = station.id;
  if(markers[key]) return;
  const m = L.marker([station.latitude, station.longitude]).addTo(map)
    .bindPopup(station.nom_station);
  markers[key] = m;
}

function showCurrent(data){
  const el = document.getElementById('currentData');
  el.textContent = JSON.stringify(data, null, 2);
}

function showReport(data){
  const el = document.getElementById('reportData');
  el.textContent = data.summary_text || 'Aucun rapport';
}

function showAlerts(list){
  const el = document.getElementById('alertsList');
  el.innerHTML = '';
  list.forEach(a=>{
    const li = document.createElement('li');
    li.textContent = `${a.niveau || ''} - ${a.type_alerte || ''}: ${a.message || ''}`;
    el.appendChild(li);
  })
}

async function loadStations(){
  const data = await fetchJSON('/regions/');
  // regions endpoint returns region objects; need to fetch stations separately
  // Instead fetch weather-stations list
  const stations = await fetchJSON('/weather-stations/');
  const select = document.getElementById('stationSelect');
  select.innerHTML = '';
  stations.results?.forEach(s=>{
    const opt = document.createElement('option');
    opt.value = s.id;
    opt.textContent = s.nom_station + ' (' + (s.region || '') + ')';
    select.appendChild(opt);
    addStationMarker(s);
  })
  // initial select
  if(select.options.length) {
    select.selectedIndex = 0;
    await onStationChange();
  }
}

async function onStationChange(){
  const select = document.getElementById('stationSelect');
  const id = select.value;
  if(!id) return;
  try{
    const current = await fetchJSON(`/weather-stations/${id}/current/`);
    showCurrent(current);
  }catch(e){
    showCurrent({error: e.message});
  }
  try{
    const report = await fetchJSON(`/weather-stations/${id}/report-today/`);
    showReport(report);
  }catch(e){
    showReport({summary_text: 'Aucun rapport'});
  }
  try{
    const alerts = await fetchJSON(`/weather-stations/${id}/active-alerts/`);
    showAlerts(alerts);
  }catch(e){
    showAlerts([]);
  }
  // load hourly last 24h
  try{
    const hourly = await fetchJSON(`/weather-stations/${id}/hourly-history/?hours=24`);
    const temps = hourly.map(h=>parseFloat(h.temperature_2m||0)).reverse();
    const labels = hourly.map(h=>new Date(h.date_heure).toLocaleTimeString()).reverse();
    renderChart(labels, temps);
  }catch(e){
    renderChart([],[]);
  }
}

let chart=null;
function renderChart(labels, data){
  const ctx = document.getElementById('historyChart').getContext('2d');
  if(chart) chart.destroy();
  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Température (°C)',
        data: data,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.2
      }]
    }
  });
}

window.addEventListener('DOMContentLoaded', ()=>{
  initMap();
  loadStations();
  document.getElementById('stationSelect').addEventListener('change', onStationChange);
});
