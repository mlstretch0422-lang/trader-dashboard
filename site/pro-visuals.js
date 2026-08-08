(() => {
  const file = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
  document.body.classList.add('pro-visuals');

  const htmlSection = (markup) => {
    const wrap = document.createElement('div');
    wrap.innerHTML = markup.trim();
    return wrap.firstElementChild;
  };

  function upgradeHome() {
    const heroProof = document.querySelector('.home-hero .beta-proof-card');
    if (heroProof && !heroProof.classList.contains('beta-terminal-card')) {
      heroProof.className = 'beta-terminal-card';
      heroProof.setAttribute('aria-label', 'Signal Bridge archived MES research shown in a trading terminal frame');
      heroProof.innerHTML = `
        <div class="pro-terminal-top">
          <div class="pro-window-dots" aria-hidden="true"><i></i><i></i><i></i></div>
          <div class="pro-terminal-title"><b>Signal Bridge</b><span>MES research desk</span></div>
          <div class="pro-terminal-live">Archived study</div>
        </div>
        <div class="pro-chart-stage">
          <img src="assets/research/mes-study-01.png" alt="Archived MES chart study from Signal Bridge research" />
          <div class="pro-chart-grid" aria-hidden="true"></div>
          <div class="pro-float-stat pro-float-a green"><span>Reconstructed sample</span><strong>+$2,381.25</strong><small>38-trade V1 research net</small></div>
          <div class="pro-float-stat pro-float-b blue"><span>Profit factor</span><strong>1.78</strong><small>same reconstructed sample</small></div>
          <div class="pro-float-stat pro-float-c violet"><span>Strategy DNA</span><strong>V1 → V6</strong><small>versions stay tied to their evidence</small></div>
          <span class="pro-chart-tag">Historical research · not live P&amp;L</span>
        </div>
        <div class="pro-terminal-tabs"><span>Chart</span><span>Session</span><span>Journal</span><span>Strategy DNA</span></div>`;
    }

    if (document.querySelector('.pro-showcase')) return;
    const proofSection = document.querySelector('.beta-gallery')?.closest('section');
    const anchor = proofSection || document.getElementById('how-it-works');
    if (!anchor) return;

    const showcase = htmlSection(`
      <section class="shell section pro-showcase" aria-label="Signal Bridge product interface preview">
        <div class="section-head"><div><span class="eyebrow">Inside the product</span><h2>Charts first. Decisions around them.</h2></div><p>The interface is being shaped like a trading desk, not a folder of notes. The chart stays central while session context, journal records, and strategy versions remain one click away.</p></div>
        <div class="pro-product-grid">
          <article class="pro-product-window large">
            <div class="pro-product-head"><strong>Morning Desk</strong><span>interface preview · illustrative layout</span></div>
            <div class="pro-product-body">
              <div class="pro-product-copy"><span class="pro-product-badge">Session map</span><h3>Price, ORB structure, context and readiness on one screen.</h3><p>The live Signals page now turns stored session-price events into a chart instead of showing only text cards.</p></div>
              <div class="pro-ui-chart" aria-label="Illustrative Morning Desk interface preview">
                <div class="range"></div><div class="mid"></div>
                <svg class="trace" viewBox="0 0 700 260" preserveAspectRatio="none" aria-hidden="true">
                  <defs><linearGradient id="proTraceGradient" x1="0" x2="1"><stop offset="0" stop-color="#4b91ff"/><stop offset=".52" stop-color="#62d8ff"/><stop offset="1" stop-color="#63e6ad"/></linearGradient><linearGradient id="proAreaGradient" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#62d8ff" stop-opacity=".16"/><stop offset="1" stop-color="#62d8ff" stop-opacity="0"/></linearGradient></defs>
                  <path class="area" d="M0 210 C70 198 95 166 150 178 C210 192 235 128 295 139 C355 150 372 91 430 104 C490 119 528 72 585 82 C628 90 655 54 700 63 L700 260 L0 260 Z"/>
                  <path d="M0 210 C70 198 95 166 150 178 C210 192 235 128 295 139 C355 150 372 91 430 104 C490 119 528 72 585 82 C628 90 655 54 700 63"/>
                </svg>
              </div>
              <div class="pro-preview-strip"><div><span>Opening range</span><b>ORH · ORM · ORL</b></div><div><span>Setup state</span><b class="mint">Readiness</b></div><div><span>Market context</span><b>News · bias</b></div><div><span>Session memory</span><b>Timeline</b></div></div>
            </div>
          </article>
          <article class="pro-product-window">
            <div class="pro-product-head"><strong>Trade Journal</strong><span>Discord → private workspace</span></div>
            <div class="pro-product-body"><div class="pro-product-copy"><h3>The screenshot belongs to the trade.</h3><p>Thesis, setup, money, R, chart and review stay attached instead of living in separate apps.</p></div><div class="pro-journal-ticket"><div class="pro-journal-thumb" aria-hidden="true"></div><div class="pro-ticket-copy"><strong>MES · ORB retest</strong><span>Original note preserved → closeout added afterward → strategy version linked.</span><div class="pro-ticket-money"><b>P&amp;L</b><b>R multiple</b></div></div></div></div>
          </article>
          <article class="pro-product-window">
            <div class="pro-product-head"><strong>Strategy DNA</strong><span>version-aware evidence</span></div>
            <div class="pro-product-body"><div class="pro-product-copy"><h3>Know which rules produced which sample.</h3><p>Strategy and indicator changes stay attached to the observations they actually generated.</p></div><div class="pro-dna-stack"><div class="pro-dna-row"><i>01</i><div><strong>Rules defined</strong><small>Location · context · trigger · invalidation</small></div><span>Versioned</span></div><div class="pro-dna-row"><i>02</i><div><strong>Indicator config</strong><small>Exact chart-tool version and settings</small></div><span>Linked</span></div><div class="pro-dna-row"><i>03</i><div><strong>Evidence grows</strong><small>Backtest → forward observations → review</small></div><span>Tracked</span></div></div></div>
          </article>
        </div>
      </section>`);
    anchor.insertAdjacentElement('afterend', showcase);
  }

  function stageProgress(stage) {
    const value = String(stage || '').toUpperCase();
    const map = { PREMARKET:12, ORB_FORMED:32, PREOPEN:46, OPEN_SNAPSHOT:56, SETUP:72, WAIT:72, ENTRY:82, SESSION_CLOSE:100 };
    return map[value] || 0;
  }

  function finite(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number : null;
  }

  function renderSessionMap(summary) {
    const map = document.getElementById('proSessionMap');
    if (!map) return;
    const svg = document.getElementById('proSessionSvg');
    const empty = document.getElementById('proSessionEmpty');
    const latest = summary?.latest || {};
    const orb = summary?.orb || {};
    const events = Array.isArray(summary?.events) ? summary.events : [];
    const priced = events.map((event, index) => ({ event, index, price: finite(event.price) })).filter((item) => item.price !== null);
    const levels = [finite(orb.orb_high), finite(orb.orb_mid), finite(orb.orb_low)].filter((value) => value !== null);
    const allPrices = [...priced.map((item) => item.price), ...levels];

    document.getElementById('proSessionTitle').textContent = summary?.session_date ? `${summary.symbol || 'MES'} · ${summary.session_date}` : 'MES · waiting for session';
    const progress = stageProgress(latest.stage);
    document.getElementById('proSessionProgressLabel').textContent = latest.stage ? `${String(latest.stage).replaceAll('_',' ')} · ${progress}%` : 'Waiting · 0%';
    document.getElementById('proSessionProgressFill').style.width = `${progress}%`;
    document.getElementById('proMapLatest').textContent = finite(latest.price) === null ? '—' : finite(latest.price).toLocaleString(undefined,{maximumFractionDigits:2});
    document.getElementById('proMapRange').textContent = finite(orb.range_points) === null ? '—' : `${finite(orb.range_points).toLocaleString(undefined,{maximumFractionDigits:2})} pts`;
    document.getElementById('proMapStage').textContent = latest.stage ? String(latest.stage).replaceAll('_',' ') : '—';
    document.getElementById('proMapEvents').textContent = String(events.length);

    if (!allPrices.length) {
      svg.innerHTML = '';
      empty.hidden = false;
      return;
    }
    empty.hidden = true;
    const W = 1000, H = 300, padX = 34, padY = 24;
    let min = Math.min(...allPrices), max = Math.max(...allPrices);
    const span = Math.max(max - min, Math.max(Math.abs(max),1) * .0015, 1);
    min -= span * .14; max += span * .14;
    const y = (price) => padY + (max - price) / (max - min) * (H - padY * 2);
    const x = (i) => priced.length <= 1 ? W / 2 : padX + i / (priced.length - 1) * (W - padX * 2);
    const points = priced.map((item,i) => `${x(i).toFixed(1)},${y(item.price).toFixed(1)}`).join(' ');
    const area = priced.length > 1 ? `${points} ${x(priced.length-1).toFixed(1)},${(H-padY).toFixed(1)} ${x(0).toFixed(1)},${(H-padY).toFixed(1)}` : '';
    const levelRows = [
      ['ORH', finite(orb.orb_high), '#62d8ff'],
      ['ORM', finite(orb.orb_mid), '#a78bfa'],
      ['ORL', finite(orb.orb_low), '#63e6ad'],
    ].filter((row) => row[1] !== null);
    const eventDots = priced.map((item,i) => {
      const side = String(item.event?.side || '').toUpperCase();
      const color = side === 'LONG' ? '#63e6ad' : side === 'SHORT' ? '#fb7185' : '#62d8ff';
      return `<circle cx="${x(i).toFixed(1)}" cy="${y(item.price).toFixed(1)}" r="4.3" fill="${color}" stroke="#07111a" stroke-width="2" />`;
    }).join('');
    const levelMarkup = levelRows.map(([label,price,color]) => `<g><line x1="0" x2="1000" y1="${y(price).toFixed(1)}" y2="${y(price).toFixed(1)}" stroke="${color}" stroke-opacity=".34" stroke-dasharray="8 8"/><text x="934" y="${(y(price)-7).toFixed(1)}" fill="${color}" class="pro-level-label">${label}</text></g>`).join('');
    svg.innerHTML = `<defs><linearGradient id="liveTrace" x1="0" x2="1"><stop offset="0" stop-color="#4b91ff"/><stop offset=".55" stop-color="#62d8ff"/><stop offset="1" stop-color="#63e6ad"/></linearGradient><linearGradient id="liveArea" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#62d8ff" stop-opacity=".18"/><stop offset="1" stop-color="#62d8ff" stop-opacity="0"/></linearGradient></defs>${levelMarkup}${priced.length>1 ? `<polygon points="${area}" fill="url(#liveArea)"/><polyline points="${points}" fill="none" stroke="url(#liveTrace)" stroke-width="3.3" stroke-linecap="round" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>` : ''}${eventDots}`;
  }

  function upgradeSignals() {
    const desk = document.querySelector('.morning-desk');
    const mission = desk?.querySelector('.mission-card');
    if (!desk || !mission || document.getElementById('proSessionMap')) return;
    const sessionMap = htmlSection(`
      <article class="pro-session-map" id="proSessionMap">
        <div class="pro-session-head"><div><span>Live session map</span><strong id="proSessionTitle">MES · waiting for session</strong></div><div class="pro-session-progress"><b id="proSessionProgressLabel">Waiting · 0%</b><div class="pro-progress-track"><div class="pro-progress-fill" id="proSessionProgressFill"></div></div></div></div>
        <div class="pro-session-chart-wrap"><svg id="proSessionSvg" viewBox="0 0 1000 300" preserveAspectRatio="none" aria-label="Stored Signal Bridge session event price trace"></svg><div class="pro-session-empty" id="proSessionEmpty"><div><strong>Waiting for the first stored price events.</strong><span>When the indicator sends real lifecycle snapshots, the chart will draw the session trace and ORB levels here.</span></div></div></div>
        <div class="pro-session-foot"><div><span>Latest stored price</span><strong class="mint" id="proMapLatest">—</strong></div><div><span>ORB range</span><strong id="proMapRange">—</strong></div><div><span>Latest stage</span><strong class="violet" id="proMapStage">—</strong></div><div><span>Session events</span><strong id="proMapEvents">0</strong></div></div>
      </article>`);
    mission.insertAdjacentElement('afterend', sessionMap);

    const baseRender = window.renderSession;
    if (typeof baseRender === 'function') {
      window.renderSession = function(summary) {
        baseRender(summary);
        renderSessionMap(summary);
      };
      if (typeof window.loadSession === 'function') window.loadSession();
    }
  }

  if (file === '' || file === 'index.html') upgradeHome();
  if (file === 'signals.html') upgradeSignals();
})();
