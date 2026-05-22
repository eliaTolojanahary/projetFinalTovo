// tabs.js — Gestion des onglets Historique / Tendances
// Charge les pages de visualisation dans un iframe en passant l'état courant
// du dashboard en query params. Pas de srcdoc, pas de postMessage.

(function () {
  const PAGES = {
    tabHistorique: {
      url: '/visualization/historique/',
      title: 'Historique — Visualisation',
      subtitle: 'Historique horaire de la station sélectionnée.'
    },
    tabTendances: {
      url: '/visualization/tendances/',
      title: 'Tendances — Visualisation',
      subtitle: 'Évolution journalière de la station sélectionnée.'
    }
  };

  const overview      = document.getElementById('tabOverview');
  const analysisPanel = document.getElementById('analysisPanel');
  const analysisFrame = document.getElementById('analysisFrame');
  const analysisTitle = document.getElementById('analysisTitle');
  const analysisSub   = document.getElementById('analysisSubtitle');
  const analysisLoad  = document.getElementById('analysisLoading');
  const tabs          = document.querySelectorAll('.tab-btn');

  let activeTabId  = null;
  let reloadTimer  = null;

  // Lit l'état courant exposé par dashboard.js
  function getState() {
    return typeof window.getDashboardState === 'function'
      ? window.getDashboardState()
      : {
          region:  document.getElementById('regionSelect')?.value  || '',
          station: document.getElementById('stationSelect')?.value || '',
          period:  document.getElementById('periodSelect')?.value  || ''
        };
  }

  function buildSrc(tabId) {
    const page = PAGES[tabId];
    const st   = getState();
    const params = new URLSearchParams();
    if (st.region)  params.set('region',  st.region);
    if (st.station) params.set('station', st.station);
    if (st.period)  params.set('period',  st.period);
    const qs = params.toString();
    return qs ? `${page.url}?${qs}` : page.url;
  }

  function showOverview() {
    overview.style.display      = 'block';
    analysisPanel.style.display = 'none';
    activeTabId = null;
  }

  function loadTab(tabId) {
    const page = PAGES[tabId];
    if (!page) { showOverview(); return; }

    activeTabId = tabId;
    overview.style.display      = 'none';
    analysisPanel.style.display = 'block';
    analysisTitle.textContent   = page.title;
    analysisSub.textContent     = page.subtitle;
    if (analysisLoad) analysisLoad.style.display = 'block';

    analysisFrame.onload = () => {
      if (analysisLoad) analysisLoad.style.display = 'none';
    };
    analysisFrame.src = buildSrc(tabId);
  }

  // Recharge l'onglet actif après un délai (déclenché par les sélecteurs)
  function scheduleReload() {
    if (!activeTabId) return;
    clearTimeout(reloadTimer);
    reloadTimer = setTimeout(() => loadTab(activeTabId), 350);
  }

  // ── Onglets ────────────────────────────────────────────────────────────────
  tabs.forEach(btn => btn.addEventListener('click', () => {
    tabs.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    if (btn.dataset.target === 'tabOverview') {
      showOverview();
    } else {
      loadTab(btn.dataset.target);
    }
  }));

  // ── Sélecteurs → recharge l'onglet ouvert ─────────────────────────────────
  ['regionSelect', 'stationSelect', 'periodSelect'].forEach(id => {
    document.getElementById(id)?.addEventListener('change', scheduleReload);
  });

  // ── Bouton Rafraîchir ─────────────────────────────────────────────────────
  document.getElementById('refreshButton')?.addEventListener('click', () => {
    if (activeTabId) loadTab(activeTabId);
  });

  // État initial : Vue générale
  showOverview();
})();