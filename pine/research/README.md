# Pine Research Workspace

This folder contains Pine scripts used to isolate strategy components. Nothing here is production-approved unless the evidence registry explicitly promotes it.

## Current script

`ES_MES_ORB_Attribution_Strategy_v1_2.pine`

Purpose:

- fix critical timing and retest defects found in v1.1
- enforce the primary 10:30 new-entry cutoff and 11:00 force-flat logic
- prevent a breakout candle from counting as its own boundary/midpoint retest
- add structural setup invalidation
- reduce management to one stop and one target
- expose clean switches for entry-mode, ORB-clock, VWAP, EMA, displacement, and range-filter attribution

## Default configuration

The defaults are a research baseline, not a trading recommendation:

- ORB: 08:00–08:15 New York
- entry window: 09:30–10:30
- force flat: 11:00
- entry mode: midpoint
- one trade per day
- displacement: off
- VWAP: off
- EMA: off
- ORB range filter: off
- stop: opposite ORB boundary
- target: 2R
- management: single stop / single target

Optional filters default off so they can be added one at a time instead of being bundled into the baseline.

## Test order

Follow `experiments/phase7/experiment_manifest.json`:

1. entry mode
2. ORB clock
3. VWAP
4. EMA
5. displacement
6. ORB range filter

Do not tune multiple layers at once.

## TradingView run procedure

For every run:

1. Copy the exact Pine file and record the Git commit.
2. Use the symbol, timeframe, and dates declared in the experiment manifest.
3. Record strategy properties, commission, slippage, quantity, and recalculation settings.
4. Change only the field named by the experiment variant.
5. Export Strategy Tester overview and list of trades.
6. Store results under a new immutable experiment output directory.
7. Write a decision that says accepted, rejected, or inconclusive.
8. Do not overwrite an older result.

## Known limitation

This repository cannot compile Pine through GitHub Actions. TradingView compilation and Strategy Tester execution still need to occur inside TradingView. A successful TradingView compile proves code validity only, not edge.

## Related documents

- `strat/PINE_CODE_AUDIT_v1_1.md`
- `strat/PHASE7_TEST_PLAN.md`
- `CONTENT_STATUS_AUDIT.md`
- `data/content-status.json`
