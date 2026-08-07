# Signal Bridge Product Polish Freeze

Status: ACTIVE
Date opened: 2026-08-07

## Why this phase exists

Signal Bridge should not leave the product layer half-finished while strategy research moves forward. The website, Discord application, journal capture, market-intelligence messages, and research workspace need to be coherent enough that the friends/family beta looks intentional and can keep recording the strategy-development journey while Pine research resumes.

This phase is product/infrastructure hardening. It does **not** promote the Mason ORB strategy, any Pine component, journal observation, or alert event to statistically validated edge.

## Product north star

One connected loop:

`market / Pine -> Signal Bridge -> Discord + durable records -> review -> research -> next strategy version -> member-facing education`

The website is the home base. Discord is the community, alert, and fast-capture surface. TradingView/Pine is the market-event source. Research evidence remains versioned and governed.

## External product research incorporated

Current public trading products were reviewed for patterns worth adapting without copying product identity:

- modern trading journals emphasize customizable dashboards, drill-down analytics, screenshots, setup tagging, periodic reports, and cross-device use;
- mature journaling products make the dashboard configurable rather than forcing one static report hierarchy;
- cloud trading platforms treat alerts/bots as always-on infrastructure and surface alerts, bots, news, and charts as one workspace;
- professional products keep navigation persistent and avoid trapping the user inside a disconnected sub-tool.

Signal Bridge should take those product lessons while remaining centered on the actual Mason trading-development workflow and evidence taxonomy.

## Current repo findings that block a product freeze

### 1. Research dashboard is structurally separate

The Pages build previously replaced native `dashboard.html` with the generated legacy/shareable dashboard. This made the Research Dashboard feel like a second website and removed the Trading OS navigation/escape path.

Target: preserve the useful console but embed it inside a native Signal Bridge workspace wrapper with OS navigation, mobile escape, and full-screen access.

### 2. Website is still too thin for a shareable beta

The core pages are strong but the product needs more native surface area:

- Indicator Library
- Reports & Research hub
- stronger personal/project identity
- clearer current-system loop
- social/community connection area
- mobile navigation polish
- consistent product visual language across native pages

### 3. Current daily market brief is not ORB intelligence

`trading_os/src/integrations/live_market_brief.py` currently builds a generic payload with a hard-coded `side="long"` and `confidence=0.85` before other modules derive simplistic direction from live price versus a reference close.

That is not a production-quality ORB read and must never be presented as strategy intelligence.

### 4. Current news brief is not an economic-calendar filter

`news_calendar_brief.py` currently retrieves up to five Yahoo Finance headlines for SPY. The file correctly labels itself as **not** an economic-calendar filter, but this is not sufficient for a professional pre-market red-news workflow.

Target: use a real economic-calendar provider with event timestamps, importance, consensus/actual/previous values, source provenance, and deterministic fail-closed behavior. Trading Economics is a strong candidate because its calendar schema exposes date/time, country, event, source, actual, previous, forecast, importance, and update timestamp. Production access requires an API key/plan, so provider selection and credentials must remain separate from the repository.

## Website freeze gates

The website is ready to pause only when:

- [x] Discord journal capture is live and private-first.
- [x] Signal event ledger is live.
- [x] Strategy Library and Mason ORB dossier exist.
- [x] Journal Intelligence exists.
- [x] Pages deploys on native `site/**` changes.
- [ ] Research Dashboard is integrated into the OS shell.
- [ ] Indicator Library is live.
- [ ] Reports & Research hub is live.
- [ ] Mobile navigation and dashboard escape are tested.
- [ ] Home page feels project-specific rather than generic SaaS.
- [ ] Discord/community and public social links are connected where appropriate.
- [ ] Footer/navigation are consistent enough for beta sharing.
- [ ] No broken links, dead-end pages, stale “future feature” copy, or contradictory status labels.
- [ ] Public/private boundaries are reviewed before broader sharing.

## Discord / bot freeze gates

The Signal Bridge Discord application should become the official product bot rather than creating extra bots without a technical reason.

Required before freeze:

- [x] Signed Discord interactions endpoint.
- [x] `/journal` private capture.
- [x] `Capture to Journal` message command.
- [ ] Product avatar/banner/about copy and consistent branded message embeds.
- [ ] `/status` for infrastructure state.
- [ ] `/orb` for latest stored ORB/session state.
- [ ] `/brief` for latest pre-market/session brief.
- [ ] `/news` for verified economic-calendar context.
- [ ] Helpful errors when current market/session data is unavailable instead of invented values.
- [ ] Message provenance and timestamps visible where useful.
- [ ] Mobile Discord output is concise and readable.

## ORB lifecycle / self-recording target

The future indicator/strategy should emit lifecycle events in addition to entry alerts so Signal Bridge can build a session record even on no-trade days.

Candidate event sequence (clock remains a research-governed strategy parameter):

1. pre-market context snapshot;
2. ORB formed: high, low, midpoint, range size;
3. pre-New-York snapshot: location versus ORB and mapped structure;
4. setup/entry/wait events during the trade window;
5. NY-AM close / forced-flat snapshot;
6. post-session outcome: which ORB side broke first, acceptance/rejection, target travel, no-trade reason, and linked journal records.

These events should be durable data, not prose only. The website and Discord bot can then read the latest session state without re-inventing strategy logic independently.

## News / calendar target

The professional news layer should separate:

- verified economic-calendar events;
- market headlines;
- strategy-specific red-news rules;
- post-release actual versus forecast/previous context.

A headline feed must never silently stand in for the economic calendar. A calendar outage must not become “no red news.”

## Strategy restart gate

Pine research resumes after the product freeze above is satisfied enough for beta use. The first Pine priority remains controlled strategy attribution, not feature accumulation:

1. ORB clock isolation;
2. entry-mode attribution;
3. filter attribution;
4. risk/cost-model reconciliation;
5. walk-forward / paper-forward evidence;
6. lifecycle events feeding Signal Bridge;
7. update website documentation from actual results.

The product should get smarter because the research gets better, not because the copy gets more confident.
