# Signal Bridge Product Moat

Status: ACTIVE PRODUCT DIRECTION  
Updated: 2026-08-07

## Core position

Signal Bridge should not compete as "another trading journal" or "another signal Discord."

The product owns the **full life of a trading idea**:

`idea -> research -> rules -> strategy version -> indicator configuration -> morning plan -> live session state -> setup -> signal / pass -> execution -> Discord note + screenshot -> journal -> session outcome -> review -> research finding -> next strategy version`

The durable connection between those stages is the product.

## Flagship differentiator: Session Story

A trading day becomes one connected object rather than several disconnected tools.

Recommended lifecycle:

1. PREMARKET — session map, higher-timeframe context, news state.
2. ORB_FORMED — high, low, midpoint, range size.
3. PREOPEN / OPEN_SNAPSHOT — location versus mapped structure, sweep/acceptance state.
4. SETUP / WAIT — setup type, direction, target, readiness conditions.
5. SIGNAL — durable TradingView event if a setup fires.
6. JOURNAL — member note, screenshot, execution record, signal link.
7. SESSION_CLOSE — first range break, target travel, outcome, no-trade reason.
8. REVIEW — lesson, adherence, evidence tags, candidate rule change.

No-trade days remain first-class session records.

## Strategy DNA

Every session/trade should eventually know which of these were active:

- strategy ID + version
- indicator ID + version
- module / preset configuration
- rules and thresholds
- setup family
- risk / exit model
- evidence stage

This enables version-aware forward comparison instead of mixing results after rules change.

Example future question:

> Since v1.7 added midpoint reclaim + HTF agreement, what changed versus v1.6 across forward observations?

## Evidence ledger

Each strategy component should retain a living evidence path such as:

`IMPLEMENTED -> BACKTESTED -> ISOLATED_ATTRIBUTION -> PAPER_FORWARD -> LIVE`

A profitable full strategy does not automatically validate each component. Removed or negative components remain in history instead of disappearing.

## Discord and website roles

### Discord = field assistant

- fast journal capture
- screenshots
- /status
- /orb
- /brief
- /news
- session prompts
- alert delivery
- member authentication handoff

### Website = memory + intelligence

- Morning Desk
- Session Story
- durable signals
- private member journal
- Strategy Lab / version history
- Indicator Workspace / presets
- evidence and research
- review and comparison

The bot reads stored Signal Bridge state. It does not invent strategy state independently.

## Beginner / experienced UX

The same backend can support two presentation modes.

### Guided

- plain-language concepts
- glossary
- first-session path
- explain why a condition matters
- setup anatomy
- risk / invalidation education

### Trader

- compact Morning Desk
- session state
- ORB / mapped levels
- news
- setup readiness
- signals
- journal
- minimal explanation

This is presentation choice, not different strategy logic.

## Setup readiness

A percentage is allowed only as **defined condition completion**, never as a win probability unless a separately validated probability model exists.

Example:

`Setup Readiness 60% = 3 of 5 defined live conditions currently present.`

The UI should allow a user to inspect exactly which conditions are complete or pending.

## Competitive research context

2026 journal products already compete heavily on trade import, screenshots, analytics, replay, AI coaching, psychology tracking, and strategy templates. Signal Bridge should not position those common features as the unique moat.

The differentiated lane is the version-aware connection between strategy research, live market state, signals, journal evidence, and the next strategy iteration.

## Product principle

**Signal Bridge does not just record what you traded. It remembers how your trading system was defined, watches how that version behaved through the session, connects your decisions to the evidence, and preserves what changed next.**
