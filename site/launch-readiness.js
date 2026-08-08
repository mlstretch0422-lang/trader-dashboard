(() => {
  const file = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
  const MEMBER_ACCESS = 'access.html';
  const MEMBER_APP = 'https://signal-bridge-webhook.airy-iris.workers.dev/member';

  function actionLink(label, href, primary = false) {
    const a = document.createElement('a');
    a.className = `btn ${primary ? 'primary' : 'secondary'}`;
    a.href = href;
    a.textContent = label;
    return a;
  }

  function replaceWorkerMemberLinks() {
    document.querySelectorAll(`a[href="${MEMBER_APP}"]`).forEach((a) => {
      a.href = MEMBER_ACCESS;
      if (/open member workspace/i.test(a.textContent || '')) a.textContent = 'Member access';
    });
  }

  function home() {
    // The lower historical-number block was useful during project review, but it
    // interrupts the product story. Keep historical evidence in Evidence/Mason.
    const moneyStrip = document.querySelector('.beta-money-strip');
    moneyStrip?.closest('section')?.remove();

    const hero = document.querySelector('.home-hero');
    const eyebrow = hero?.querySelector('.eyebrow');
    if (eyebrow) eyebrow.textContent = 'One workspace for the full trade loop';

    const actions = hero?.querySelector('.hero-actions');
    if (actions) {
      [...actions.querySelectorAll('a')].forEach((a) => {
        if (/member workspace|member access/i.test(a.textContent || '')) {
          a.href = MEMBER_ACCESS;
          a.textContent = 'Member access';
        }
      });
    }

    // Premium cards should route to the page that explains the tool; member-only
    // actions are exposed from those pages through the access flow.
    document.querySelectorAll('.premium-card').forEach((card) => {
      const title = card.querySelector('h3')?.textContent?.trim();
      if (title === 'Strategy Lab') card.href = 'strategies.html#strategy-lab';
      if (title === 'Indicator Workspace') card.href = 'indicators.html#premium-workspace';
    });
  }

  function strategies() {
    const hero = document.querySelector('.page-hero, .research-hero');
    const title = hero?.querySelector('h1');
    if (title) title.innerHTML = '<span class="gradient-text">Turn a setup into rules you can test.</span>';
    const description = hero?.querySelector('p');
    if (description) description.textContent = 'The Strategy Playbook breaks a trade into the pieces that matter: location, context, trigger, invalidation, target, risk, and pass conditions. Use the library to learn the mechanics, then use Strategy Lab to preserve your own rules and versions.';

    const lab = document.getElementById('strategy-lab') || [...document.querySelectorAll('section')].find((s) => /Strategy Lab/.test(s.querySelector('.eyebrow')?.textContent || ''));
    if (lab && !lab.querySelector('.launch-member-action')) {
      const row = document.createElement('div');
      row.className = 'hero-actions launch-member-action';
      row.appendChild(actionLink('Open member Strategy Lab →', 'access.html?tool=strategy-lab', true));
      lab.appendChild(row);
    }
  }

  function indicators() {
    const premium = document.getElementById('premium-workspace') || [...document.querySelectorAll('section')].find((s) => /Premium Workspace/.test(s.querySelector('.eyebrow')?.textContent || ''));
    if (premium && !premium.querySelector('.launch-member-action')) {
      const row = document.createElement('div');
      row.className = 'hero-actions launch-member-action';
      row.appendChild(actionLink('Open member Indicator Workspace →', 'access.html?tool=indicator-workspace', true));
      premium.appendChild(row);
    }
  }

  function journal() {
    const hero = document.querySelector('.journal-hero');
    if (hero && !hero.querySelector('.launch-member-action')) {
      const row = document.createElement('div');
      row.className = 'hero-actions launch-member-action';
      row.style.marginTop = '18px';
      row.appendChild(actionLink('Open private journal →', 'access.html?tool=journal', true));
      row.appendChild(actionLink('See the Discord workflow', '#add-a-trade'));
      hero.appendChild(row);
    }

    // The private workspace is already live; don't describe it as a future item.
    document.querySelectorAll('.card').forEach((card) => {
      const h3 = card.querySelector('h3')?.textContent?.trim();
      if (h3 === 'Private member workspace') {
        card.querySelector('.chip')?.replaceChildren(document.createTextNode('Live'));
        const p = card.querySelector('p');
        if (p) p.textContent = 'Each Discord-linked member can open a private website workspace containing only their own journal history, screenshots, results, and strategy links.';
      }
      if (h3 === 'Signal + strategy linkage') {
        card.querySelector('.chip')?.replaceChildren(document.createTextNode('Foundation live'));
      }
    });
  }

  replaceWorkerMemberLinks();
  if (file === '' || file === 'index.html') home();
  if (file === 'strategies.html') strategies();
  if (file === 'indicators.html') indicators();
  if (file === 'journal.html') journal();
})();
