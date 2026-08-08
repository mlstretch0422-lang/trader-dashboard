# Signal Bridge Product Audit — 2026-08-08

## North star
Signal Bridge is not a public folder of Mason's trading research. It is a trading operating system that should help a trader move from idea → plan → live session → execution/pass → journal → review → evidence → next strategy version.

The flagship Mason system is the first deeply documented model inside the product. The product itself must remain useful to someone who trades a different setup.

## Current build order
1. Website/product experience
2. Discord bot + hosted backend reliability and usefulness
3. Indicator / Pine visual and lifecycle sensor
4. Mechanical strategy Pine + controlled testing
5. Real Monday trading-day proof of the end-to-end loop

Do not restart feature sprawl before these layers are coherent.

## Who the product must work for
### New trader
Needs to understand what Signal Bridge is within ~30 seconds, see charts/trades/money immediately, understand the basic workflow, and know what to click next without knowing ORB/FVG/MSS vocabulary first.

### Experienced discretionary trader
Needs a fast desk: chart/session state, levels, readiness, news/calendar, signals, journal capture, strategy versions, evidence, and minimal explanation.

### Premium/member trader
Needs private identity, journal history, screenshots, strategy versions, indicator configuration, signals, session history, and eventually data tied together by account/user ownership.

### Mason / flagship desk
Needs the actual trading system, Trade Bible, ORB model, research lineage, backtests, forward observations, indicator versions, and strategy changes preserved without mixing them into generic platform education.

---

# What external beta feedback exposed
Two independent themes have now appeared in friend review:

1. **"Where are the charts, money and lines?"**
   - The site looked polished but too much like documentation.
   - The visitor had to read before feeling that this was trading software.

2. **"What do I actually do?"**
   - The product was understood as some kind of journal, but the user could not immediately tell whether to log a trade before or after, how to test an online trade idea, or what the system did with it afterward.

3. **"How much AI did you use?"**
   - The product should not visually or verbally feel like a generic AI-generated SaaS template.
   - AI/automation can assist development and analysis under the hood, but the public identity should be trading software: charts, records, rules, money, screenshots, strategy versions, evidence, session context and community.

These are product findings, not copy-edit comments.

---

# Competitive benchmark — what established products teach us
Reviewed 2026-08-08.

## TradeZella
Observed strengths:
- Dashboard begins with trading metrics and performance widgets.
- Trade page makes the chart central and keeps notes, executions, attachments and running P&L around it.
- Beginner onboarding explains layout and workflow explicitly.
- Backtesting is treated as a dedicated product area rather than a pile of source files.

Useful lesson for Signal Bridge:
**show the trade first, then the explanation.**

References:
- https://help.tradezella.com/en/articles/13863136-getting-started-with-tradezella
- https://help.tradezella.com/en/articles/5860216-understanding-the-trade-page
- https://help.tradezella.com/en/articles/7118437-understanding-dashboard-widgets-and-stats

## TraderSync
Observed strengths:
- Interactive price-action charts with entry/exit points.
- Running P&L, target/stop visuals, screenshot attachments, setup and mistake tagging.
- Customizable dashboards with many widgets and responsive device support.
- Performance reporting lets traders compare setups instead of only storing diary text.

Useful lesson for Signal Bridge:
**journal records should become analyzable trade objects, not chat archives.**

References:
- https://tradersync.com/features/
- https://tradersync.com/trading-journal/

## TrendSpider
Observed strengths:
- Chart is the center of the product experience.
- Dashboards operate as configurable control centers containing charts, scanners, alerts, bots, news and other widgets.
- The product presents data visually before asking the user to read documentation.

Useful lesson for Signal Bridge:
**Morning Desk should be a command center, not a row of explanatory cards.**

References:
- https://trendspider.com/product/
- https://help.trendspider.com/kb/workspaces/dashboards

---

# Current state scorecard
Scores are product-readiness judgments, not statistical strategy ratings.

| Area | Current | Target before wider beta | Main issue |
| --- | ---: | ---: | --- |
| Core product architecture | 8/10 | 9/10 | Strong backend spine; needs more lived end-to-end sessions |
| First-30-second clarity | 6/10 | 9/10 | Improving, but still too much explanation before payoff |
| Visual trading identity | 5/10 | 9/10 | Raw research screenshots made the site look like a project folder |
| Mobile usability | 7/10 | 9/10 | Structure is responsive; visual hierarchy still needs real-device review |
| Journal backend | 8/10 | 9/10 | Strong private/publish/member model; needs final real user flow verification |
| Journal product UX | 6/10 | 9/10 | Need richer trade-detail view and simpler upload/closeout experience |
| Session intelligence | 7/10 | 9/10 | Durable lifecycle exists; needs real Pine-fed market sessions |
| Live Signals experience | 7/10 | 9/10 | Session map/readiness good direction; value limited until real feed fills |
| Discord bot | 8/10 | 9/10 | Commands/backend are strong; final /start deployment and real-use polish remain |
| Premium identity/access | 7/10 | 9/10 | Discord-linked member layer exists; role gating and member UX can deepen later |
| Strategy Lab | 6/10 | 9/10 | Real backend spine exists; user-facing creation/testing experience is early |
| Indicator Workspace | 6/10 | 9/10 | Product concept clear; Pine v1.3 still needs TradingView compile + visual tuning |
| Mason flagship system | 8/10 | 9/10 | Separation is much better; next gains come from real current-session examples |
| Research & Evidence | 8/10 | 9/10 | Strong source discipline; presentation needs more graphs and fewer raw artifacts |
| Product differentiation | 8/10 concept / 5/10 visible | 9/10 | Strategy DNA + Session Story are unique; UI must make them obvious |

---

# Product differentiation we should protect
## 1. Session Story
A trading day should become one durable story:
- Premarket context
- ORB formed
- Pre-open state
- NY open location
- Setup / wait state
- Signal or pass
- Execution / screenshot
- Session close
- Result
- Lesson / review

A no-trade day still creates useful data.

## 2. Strategy DNA
Every trade/session should know:
- strategy name/version
- indicator version
- relevant settings
- setup family
- rules active at the time
- evidence stage

This allows Signal Bridge to answer: **what changed when the strategy changed?**

## 3. Discord fast layer + website memory layer
Discord is for fast capture, alerts, briefs, session interaction and community.
Website/member workspace is for durable records, analytics, strategy versions and review.

## 4. Evidence grows with the trader
A component can move through:
PROJECT RULE → IMPLEMENTED → BACKTESTED → ISOLATED ATTRIBUTION → WALK-FORWARD → PAPER/FORWARD → LIVE

The platform should remember failures and removals, not only winners.

---

# Visual standard — effective immediately
Public-facing product visuals must fit one of these categories:

## A. Product interface visual
Use when selling/explaining the product.
Examples: Morning Desk, trade-detail journal, Strategy DNA, indicator workspace.

Rules:
- clean crop / designed frame
- no random desktop clutter
- no unrelated company branding
- clear visual hierarchy
- chart/data visible immediately
- demo values explicitly identified when illustrative

## B. Educational setup visual
Use when teaching a concept.
Examples: ORB reclaim, liquidity sweep, FVG reaction, MSS/displacement, invalidation.

Rules:
- one setup per image
- entry/stop/target obvious
- labels should explain mechanics, not hype
- a visitor should understand the picture before reading the paragraph

## C. Evidence visual
Use when supporting a historical/research claim.
Examples: strategy equity comparison, drawdown curve, trade distribution, real trade screenshot, source export.

Rules:
- historical/replay/paper/live status visible
- source/period/sample visible
- avoid third-party logos on marketing surfaces when possible
- raw source screenshots belong lower in Evidence, not in the homepage hero

### What no longer qualifies as a product visual
- random source-folder screenshot
- full desktop capture with unrelated branding/UI
- weak chart with no obvious setup
- screenshot included only because it exists
- spreadsheet/export presented as a hero graphic

---

# Current product architecture
## Public / discovery
### Home
Role: explain Signal Bridge in 30 seconds and make the product desirable.
Must show: chart/trade visual, money/result visual, simple workflow, Premium/member path, flagship model, community.

### Strategies
Role: generic setup/playbook education and Strategy Lab entry point.
Must not become Mason's backtest history page.

### Indicators
Role: chart-tool architecture and indicator workspace.
Must show what the tool looks like on price, not repeat strategy prose.

### Signals
Role: live Morning Desk + session intelligence + durable alert history.
Should feel like the daily command center.

### Journal
Role: explain and demonstrate before-trade capture, finished-trade capture, screenshot, P&L/R, closeout and review.

### Mason
Role: flagship trader/system entry point.
Contains Mason ORB, Trade Bible, research/evidence and strategy history.

## Member / private
### Member home
Role: authenticated premium workspace.

### My Journal
Role: member-owned private records + screenshots + review/publish state.

### Strategy Lab
Role: member-owned strategy definitions and durable versions.

### Future member layers
- indicator presets/configurations
- signal entitlements
- personalized dashboard widgets
- deeper journal analytics
- strategy comparisons

---

# Immediate gaps by page
## Home
- Product visuals were too dependent on raw research captures.
- Replace them with designed Signal Bridge trade/session/journal visuals.
- Keep historical metrics, but move raw artifacts to Evidence.

## Signals
- Session Map direction is correct.
- Needs real Pine-fed lifecycle data.
- When no live data exists, demo/preview state must be clearly marked rather than looking broken.
- Eventually include daily P&L / trade count / session outcome when member records exist.

## Strategies
- Content architecture is good.
- Needs annotated chart examples per setup family.
- Strategy Lab should become obviously actionable from this page.

## Indicators
- Needs actual TradingView screenshots once v1.3 compiles.
- Until then, designed product previews are acceptable if labeled illustrative.
- Strategy logic vs visual/context module distinction must stay explicit.

## Journal
- Backend is ahead of UI.
- Need a richer trade-detail page with chart, result, P&L/R, original thesis, closeout, tags and Strategy DNA.
- Private member view should become the primary experience, public Journal the explanation/demo.

## Evidence
- Strong information, weak visual storytelling.
- Add equity curves, distribution charts, version comparisons and clean evidence cards.
- Raw third-party/source screenshots can remain available but should not dominate.

## Mason ORB
- Core page is good.
- Needs real current winning/losing case studies from forward sessions as they accumulate.
- Designed setup anatomy is fine as an educational visual, but must not masquerade as historical trade proof.

---

# Backend / bot checkpoint
Already built:
- durable signal ledger
- private journal capture
- publish/private controls
- member Discord identity/login
- member journal
- Strategy Lab/version storage
- Strategy DNA tables and session linking
- session lifecycle ledger
- market intelligence cache/provider layer
- `/status`, `/orb`, `/brief`, `/news`
- bulk Discord command registration
- `/journal-update`
- `/start` onboarding code merged

Still to do before calling bot layer finished:
1. Bundle/deploy final `/start` command polish.
2. Run one clean friend/new-user command test.
3. Choose/configure economic calendar provider when acceptable.
4. Confirm scheduled morning/session delivery tone and channel behavior.
5. Feed real Pine lifecycle events and verify `/orb` + `/brief` with a real session.

---

# Pine / indicator checkpoint
Current staged visual candidate: `ES_ORB_Indicator_v1_3_VISUAL_STACK.pine`.

Purpose:
- chart sensor + execution-support visual tool
- ORB structure
- liquidity/context levels
- VWAP/EMA context
- optional reference sessions
- clean signal markers
- decision panel
- lifecycle alerts to Signal Bridge

Important next step:
**TradingView compile and visual review.** GitHub CI cannot validate Pine compilation.

Do not change the strategy rules during the first visual compile/debug pass unless a compile/runtime bug forces it.

---

# Next execution plan
## Phase 1 — Product visual cleanup (NOW)
- Remove raw research screenshots from product-facing hero/showcase positions.
- Use designed Signal Bridge visuals for trade, journal, session desk and Strategy DNA.
- Keep raw artifacts in Evidence.
- Make each page show its job visually near the top.

## Phase 2 — Goals/current-state review (THIS AUDIT)
- Use this document as the checkpoint instead of re-litigating architecture every page review.
- Future changes should answer one of the identified gaps.

## Phase 3 — Finish bot deployment
- Deploy the already-merged `/start` polish in the next bundled Worker sync.
- Do not force repeated terminal deploys for tiny changes.

## Phase 4 — TradingView indicator compile
- Compile v1.3.
- Fix Pine errors only.
- Then review chart cleanliness on MES/ES 1m/5m/15m.
- Capture clean real screenshots for the website after it looks professional.

## Phase 5 — Monday end-to-end session proof
Run one complete day through:
1. premarket analysis text + screenshot
2. Pine session lifecycle
3. Morning Desk
4. Discord `/brief` + `/orb` + `/news`
5. trade or no-trade decision
6. journal screenshot/result
7. website/member record
8. session close/review
9. Strategy DNA linkage

Document every failure/friction point.

## Phase 6 — Mechanical strategy Pine
Only after the indicator/session sensor is reliable:
- align strategy code to the actual discretionary decision process
- run controlled backtest/attribution variants
- compare against source-of-truth results
- keep research stages separate

---

# Definition of "ready for friends/family beta"
The beta is ready to hand to someone without explaining it live when:
- homepage makes sense in 30 seconds
- mobile shows chart/trading visuals immediately
- `/start` explains Discord workflow
- member login works
- journal capture + update + screenshot + private viewing works
- Morning Desk shows either real data or an explicit demo/empty state
- one real session has completed the full lifecycle
- v1.3 indicator compiles and looks clean
- no public page exposes private records or proprietary secrets
- product visuals do not look like raw project-folder screenshots

# Definition of "ready to sell"
Not the current milestone. Later requirements include:
- private/proprietary source split
- real role/billing entitlement
- stable member UX
- durable screenshot storage
- terms/privacy/support flows
- reliable market-data/calendar provider
- broader real-user testing
- documented strategy access/licensing rules
- production monitoring and recovery procedures
