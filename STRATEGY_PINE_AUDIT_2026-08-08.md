# Signal Bridge Strategy Pine Audit — 2026-08-08

## Scope
This audit compares the checked-in `ES_ORB_Strategy_v1_1_FIXED.txt` with the current Signal Bridge product requirements. It does not reinterpret historical results and does not declare a new edge.

## Critical finding: force-flat clock
The v1.1 strategy defines:

`f_inWindow(i_flatTime, i_flatTime)`

When the start and end minute are equal, the overnight branch of `f_inWindow()` resolves to `cur >= start OR cur < end`, which is effectively true for the whole day. The later rising-edge expression therefore cannot reliably detect the requested 11:00 force-flat transition.

### v1.2 correction
The staged v1.2 strategy introduces `f_reachedTime()` and triggers force-flat on the first chart bar whose timestamp reaches/crosses the configured flat minute on the same trading date.

This is a mechanical code correction. It means v1.2 needs a fresh matched historical run; v1.1/V6 result rows must not be silently transferred to v1.2.

## Preserved strategy mechanics
The v1.2 staged script intentionally preserves the v1.1 default mechanics:
- ORB: 08:00–08:15 New York
- New entries: 09:30–11:00 New York
- One trade per day
- Breakout displacement threshold: body >= 35% ORB range OR 0.75 ATR
- Retest mode default: midpoint
- VWAP alignment ON by default
- EMA alignment OFF by default
- ORB range 5–50 points
- Stop default: opposite ORB boundary
- Three R-based targets with 50/30/20 requested exit percentages
- Staircase stop behavior retained

No new confluence was promoted to a strategy rule in this correction.

## Signal Bridge integration change
v1.2 order alerts now emit the same core fields expected by the hosted Signal Bridge event path:
- symbol
- side
- event
- price
- strategy
- strategy_version_id
- note
- time

Strategy identity:
- Name: `Mason ORB Strategy`
- Version: `1.2-signal-bridge`
- Strategy DNA ID: `mason-orb-v1.2-signal-bridge`

## Open verification item: partial exits on one futures contract
The strategy defaults to one fixed unit while requesting 50% / 30% / 20% exits. Before treating new strategy results as comparable evidence, TradingView's broker-emulator handling of those partial percentages on ES/MES must be explicitly checked.

Why it matters:
- If the emulator rounds/reserves quantities differently than an executable one-contract trade, target distribution and staircase behavior can differ from intended execution.
- Multi-target behavior may require a multi-contract test configuration or a separate single-contract execution mode.

Status: **UNRESOLVED / TESTING ITEM**. Do not silently assume the existing percentage exits are realistic for one MES contract.

## Required next checks
1. Compile `ES_ORB_Indicator_v1_3_VISUAL_STACK.pine` in TradingView.
2. Compile `ES_ORB_Strategy_v1_2_SIGNAL_BRIDGE.pine` in TradingView.
3. Confirm 11:00 force-flat on 1m / 5m / 15m charts.
4. Confirm ORB formation timestamps and timezone behavior.
5. Confirm one-trade-per-day state reset.
6. Verify partial-exit quantity behavior for one MES contract.
7. Run a matched v1.1 vs v1.2 historical comparison with identical instrument, timeframe, dates, commissions, slippage and settings.
8. Only then decide whether v1.2 can become the shareable mechanical strategy baseline.

## Evidence status
- v1.1: historical source / existing backtest lineage
- v1.2 Signal Bridge: IMPLEMENTED in source, **STAGED**, not yet TradingView-compiled in this repository workflow
- force-flat correction: code-level defect identified and corrected; runtime verification still required
