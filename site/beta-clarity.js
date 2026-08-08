(() => {
  const file = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
  const memberUrl = 'https://signal-bridge-webhook.airy-iris.workers.dev/member';

  function section(html) {
    const wrap = document.createElement('div');
    wrap.innerHTML = html.trim();
    return wrap.firstElementChild;
  }

  function home() {
    document.getElementById('welcomeGate')?.remove();
    document.getElementById('modeSwitch')?.remove();

    const hero = document.querySelector('.home-hero');
    if (!hero) return;
    const eyebrow = hero.querySelector('.eyebrow');
    const title = hero.querySelector('h1');
    const description = hero.querySelector('#heroDescription') || hero.querySelector('p');
    const actions = hero.querySelector('.hero-actions');
    if (eyebrow) eyebrow.textContent = 'Charts · trades · money · strategy evidence';
    if (title) title.innerHTML = '<span class="gradient-text">See the setup. Save the trade. Track the result. Prove what actually works.</span>';
    if (description) description.textContent = 'Signal Bridge is a trading workspace for the whole loop: live session context, chart tools, alerts, trade capture, P&L, screenshots, and strategy testing. It is built to answer one practical question over time: which setups are actually earning their place in your playbook?';
    if (actions) actions.innerHTML = `<a class="btn primary" href="signals.html#morning-desk">See the live desk →</a><a class="btn secondary" href="#how-it-works">How do I use this?</a><a class="btn secondary" href="${memberUrl}">Open Member Workspace</a>`;

    const consolePanel = hero.querySelector('.hero-console');
    if (consolePanel) {
      consolePanel.className = 'beta-proof-card';
      consolePanel.setAttribute('aria-label', 'Real Signal Bridge trading research');
      consolePanel.innerHTML = `
        <div class="beta-proof-head"><b>Archived MES chart study</b><span>real project research</span></div>
        <img src="assets/research/mes-study-01.png" alt="Archived MES chart study from Signal Bridge research" />
        <div class="beta-proof-metrics">
          <div><strong>38 trades</strong><span>reconstructed V1 sample</span></div>
          <div><strong>+$2,381.25</strong><span>V1 reconstructed net</span></div>
          <div><strong>PF 1.78</strong><span>same reconstructed sample</span></div>
        </div>
        <div class="beta-proof-foot">Historical research sample, not live performance. Different tests stay separate instead of being blended into one marketing number.</div>`;
    }

    const how = section(`
      <section class="shell section beta-clarity-section" id="how-it-works">
        <div class="section-head"><div><span class="eyebrow">What do I actually do?</span><h2>Start with a trade idea. End with evidence.</h2></div><p>You can use your own setup, something from Discord, a video you saw, or a model you are testing. Signal Bridge records the decision and the outcome so the idea can be judged over a sample instead of by one screenshot.</p></div>
        <div class="beta-use-grid">
          <article class="beta-use-card"><span class="num">01</span><h3>Have an idea</h3><p>Write the setup, where the idea came from, what has to happen, and what would prove it wrong. An online call is a hypothesis until your own data says otherwise.</p></article>
          <article class="beta-use-card"><span class="num">02</span><h3>Save the trade</h3><p>After the trade, run <code>/journal</code> and add the chart, result, P&amp;L and R. Before the trade, save it as <code>OPEN</code> so the original thesis is preserved.</p></article>
          <article class="beta-use-card"><span class="num">03</span><h3>Close the loop</h3><p>If you logged it before entry, use <code>/journal-update</code> afterward to add the result, money, R multiple and review without overwriting the original note.</p></article>
          <article class="beta-use-card"><span class="num">04</span><h3>Build a sample</h3><p>Group repeated trades by setup and strategy version. One winner does not validate a creator or a strategy. A consistent, clearly defined sample starts to tell you something.</p></article>
        </div>
        <div class="beta-truth-callout"><strong>The point:</strong> Signal Bridge does not stamp “VALID” on a person because a trade won. It keeps the rules, chart, decision, result and strategy version attached so you can evaluate the setup over repeated observations.</div>
        <div class="beta-direct-cta"><a class="btn primary" href="journal.html">Show me how to log a trade →</a><a class="btn secondary" href="strategies.html">Browse the setup playbook</a></div>
      </section>`);
    hero.insertAdjacentElement('afterend', how);

    const proof = section(`
      <section class="shell section">
        <div class="section-head"><div><span class="eyebrow">Charts &amp; numbers</span><h2>Show the work, not just the software.</h2></div><p>These are real checked-in research assets from the project. They are presented with their own sample labels so a visitor can see what was actually tested without confusing historical research with live results.</p></div>
        <div class="beta-gallery">
          <figure><img src="assets/research/mes-study-02.png" alt="Archived MES strategy chart study" /><figcaption><b>MES setup study.</b> Archived qualitative chart work used while the ORB/retest framework was being refined.</figcaption></figure>
          <figure><img src="assets/research/Tradezella-Summary-June-26-2026.png" alt="Historical TradeZella summary screenshot" /><figcaption><b>Historical journal snapshot.</b> A real project artifact — useful context, not a claim of current live profitability.</figcaption></figure>
        </div>
        <div class="beta-money-strip">
          <div><b>+$2,381.25</b><span>Reconstructed V1 net across 38 trades.</span><small>historical research</small></div>
          <div><b>1.78 PF</b><span>Reconstructed V1 profit factor.</span><small>low-confidence sample</small></div>
          <div><b>+$32,750</b><span>V6 ES 15m historical configuration.</span><small>156-trade config</small></div>
          <div><b>1.431 PF</b><span>V6 ES 15m historical configuration.</span><small>not live proof</small></div>
        </div>
      </section>`);
    how.insertAdjacentElement('afterend', proof);

    document.querySelectorAll('h3').forEach((node) => {
      if (node.textContent.trim() === 'Journal Intelligence') node.textContent = 'Trade Journal';
    });
    document.querySelectorAll('.console-stat span').forEach((node) => {
      if (node.textContent.trim() === 'Session Intelligence') node.textContent = 'Session Tracking';
      if (node.textContent.trim() === 'Market Intel') node.textContent = 'News & Calendar';
    });
  }

  function journal() {
    const hero = document.querySelector('.journal-hero');
    if (!hero) return;
    const breadcrumb = hero.querySelector('.breadcrumb');
    const eyebrow = hero.querySelector('.eyebrow');
    const title = hero.querySelector('h1');
    const description = hero.querySelector('p');
    if (breadcrumb) breadcrumb.innerHTML = '<a href="index.html">Signal Bridge</a> / Trade Journal';
    if (eyebrow) eyebrow.textContent = 'Before the trade or after it — just close the loop';
    if (title) title.innerHTML = '<span class="gradient-text">Save the trade. Keep the chart. Track the money.</span>';
    if (description) description.textContent = 'The journal is the capture layer: your original idea, screenshot, setup, result, P&L and review stay together. Log a finished trade in one shot, or save the thesis before entry and update the result afterward.';

    const guide = section(`
      <section class="shell section beta-clarity-section" id="add-a-trade">
        <div class="section-head"><div><span class="eyebrow">How to add a trade</span><h2>Two normal ways to use it.</h2></div><p>You do not need to “upload” a spreadsheet. Discord is the fast input. The private member workspace is where your records live afterward.</p></div>
        <div class="beta-journal-how">
          <article class="beta-journal-option"><span class="label">After the trade</span><h3>Log the whole thing once.</h3><p>Use <code>/journal</code>, write what happened, then add the symbol, side, setup, result, P&amp;L, R multiple and chart screenshot. It saves privately by default.</p><span class="command">/journal note:"ORB retest after liquidity sweep" symbol:MES side:LONG result:WIN pnl:185 rr:2.1 chart:[screenshot]</span></article>
          <article class="beta-journal-option"><span class="label">Before the trade</span><h3>Preserve the thesis first.</h3><p>Use <code>/journal</code> with result <code>OPEN</code>. After the trade, grab the journal ID from the receipt or inbox and use <code>/journal-update</code>. The original note stays intact.</p><span class="command">/journal-update id:12ab34cd result:LOSS pnl:-95 rr:-1 review:"entered before reclaim fully held"</span></article>
          <article class="beta-journal-option"><span class="label">Already posted it</span><h3>Capture a Discord message.</h3><p>If you already typed the trade and attached a screenshot in Discord, use <code>Capture to Journal</code> on that message. Signal Bridge stores the original post instead of making you type it again.</p><span class="command">Message menu → Apps → Capture to Journal</span></article>
          <article class="beta-journal-option"><span class="label">Review it</span><h3>Open your private workspace.</h3><p>Use <code>/member-login</code> for a one-time sign-in link. Your private journal and Strategy Lab are tied to your Discord identity.</p><span class="command">/member-login</span></article>
        </div>
        <div class="beta-truth-callout"><strong>Saw a trade idea online?</strong> Put where it came from in the original note. Track the setup repeatedly. Signal Bridge evaluates the pattern you defined; a single winning screenshot does not validate the person who posted it.</div>
      </section>`);

    const status = document.querySelector('.journal-status-grid');
    if (status) {
      hero.insertAdjacentElement('afterend', guide);
      const details = document.createElement('details');
      details.className = 'beta-system-details';
      details.innerHTML = '<summary>Technical system status</summary>';
      status.parentNode.insertBefore(details, status);
      details.appendChild(status);
    } else {
      hero.insertAdjacentElement('afterend', guide);
    }

    document.querySelectorAll('h2').forEach((node) => {
      if (node.textContent.trim() === 'Write once. Reuse everywhere.') node.textContent = 'Capture once. Review it later.';
    });
    document.querySelectorAll('.eyebrow').forEach((node) => {
      if (node.textContent.trim() === 'Capture Architecture') node.textContent = 'Journal workflow';
    });
  }

  if (file === 'index.html' || file === '') home();
  if (file === 'journal.html') journal();
})();