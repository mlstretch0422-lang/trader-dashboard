(() => {
  const file = (location.pathname.split('/').pop() || 'index.html').toLowerCase();

  function section(markup) {
    const wrap = document.createElement('div');
    wrap.innerHTML = markup.trim();
    return wrap.firstElementChild;
  }

  const visual = (src, title, copy, tag = 'Product preview') => `
    <figure class="v2-feature-visual">
      <div class="v2-visual-head"><strong>${title}</strong><span>${tag}</span></div>
      <img src="${src}" alt="${title}" loading="lazy" />
      <figcaption>${copy}</figcaption>
    </figure>`;

  function replaceHomeHero() {
    const terminal = document.querySelector('.home-hero .beta-terminal-card');
    if (!terminal) return;
    const title = terminal.querySelector('.pro-terminal-title');
    const live = terminal.querySelector('.pro-terminal-live');
    const stage = terminal.querySelector('.pro-chart-stage');
    if (title) title.innerHTML = '<b>Signal Bridge</b><span>trade workspace</span>';
    if (live) live.textContent = 'Product preview';
    if (stage) {
      stage.innerHTML = `<img class="v2-hero-product" src="assets/product/hero-trade-win.svg" alt="Illustrative Signal Bridge winning-trade workspace with ORB, entry, stop, target and result" />`;
    }
    const tabs = terminal.querySelector('.pro-terminal-tabs');
    if (tabs) tabs.innerHTML = '<span>Chart</span><span>Morning Desk</span><span>Journal</span><span>Strategy DNA</span>';
  }

  function removeHomeDuplicateShowcase() {
    // Product screenshots belong on the pages they explain. Home keeps one strong
    // hero visual and routes visitors into the product instead of repeating the
    // Journal / Strategy DNA / desk imagery they will see after clicking through.
    document.querySelector('.pro-showcase')?.remove();
  }

  function cleanResearchGallery() {
    const gallery = document.querySelector('.beta-gallery');
    const sectionEl = gallery?.closest('section');
    if (!sectionEl) return;
    const head = sectionEl.querySelector('.section-head');
    if (head) {
      const eyebrow = head.querySelector('.eyebrow');
      const h2 = head.querySelector('h2');
      const p = head.querySelector('p');
      if (eyebrow) eyebrow.textContent = 'Historical strategy research';
      if (h2) h2.textContent = 'Historical numbers, kept separate from the product demo.';
      if (p) p.textContent = 'Source files remain preserved in Research & Evidence. Home keeps only the clean historical summary instead of repeating raw research artifacts.';
    }
    gallery.remove();
    const strip = sectionEl.querySelector('.beta-money-strip');
    if (strip) strip.classList.add('v2-historical-strip');
    if (!sectionEl.querySelector('.v2-evidence-link')) {
      const link = section('<div class="v2-evidence-link"><span>Want the full research trail?</span><a href="evidence.html">Open Research &amp; Evidence →</a></div>');
      sectionEl.appendChild(link);
    }
  }

  function addPageVisual(src, title, copy, tag) {
    const hero = document.querySelector('.page-hero, .journal-hero, .research-hero, .strategy-hero, .indicator-hero');
    if (!hero || document.querySelector('.v2-page-visual-wrap')) return;
    const wrap = section(`<section class="shell v2-page-visual-wrap">${visual(src, title, copy, tag)}</section>`);
    hero.insertAdjacentElement('afterend', wrap);
  }

  function decoratePage() {
    if (file === '' || file === 'index.html') {
      replaceHomeHero();
      removeHomeDuplicateShowcase();
      cleanResearchGallery();
      return;
    }
    if (file === 'journal.html') addPageVisual('assets/product/journal-trade-detail.svg', 'A journal entry should look like the trade.', 'One record can hold the thesis, chart, setup, P&L, R multiple, result, screenshot and review. Demo values are illustrative.', 'Illustrative member record');
    if (file === 'strategies.html') addPageVisual('assets/product/hero-trade-win.svg', 'Strategy mechanics should be visible.', 'The Playbook is about location, context, trigger, invalidation and target — the chart should make those jobs obvious before the explanation does.', 'Illustrative setup anatomy');
    if (file === 'indicators.html') addPageVisual('assets/product/session-desk.svg', 'The indicator is the chart sensor.', 'ORB structure, liquidity, VWAP/EMA context, decision state and lifecycle output belong around price rather than in a wall of copy.', 'Illustrative chart-tool preview');
    if (file === 'mason-orb.html') addPageVisual('assets/product/hero-trade-win.svg', 'Mason ORB — clean setup anatomy.', 'A product-facing example of sweep, reclaim, entry, invalidation and target. Demo money is illustrative; the strategy history remains separate in Evidence.', 'Illustrative setup example');
    if (file === 'evidence.html') addPageVisual('assets/product/strategy-dna.svg', 'Evidence should connect to the exact version that created it.', 'Research is more useful when rules, indicator settings and observations stay attached instead of becoming disconnected screenshots and spreadsheets.', 'Strategy DNA preview');
  }

  decoratePage();
})();