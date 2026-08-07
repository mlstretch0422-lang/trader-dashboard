# Strategy Asset Map

Date: 2026-07-03
Goal: Map existing strategy assets (Lux/ICT/RP/TJR + your custom files) into testable optimizer components.

## Canonical Engine Files
- `trading_os/experiments/orb_v2_optimizer.py`
- `trading_os/experiments/run_forced_short_search.py`
- `trading_os/src/strategies/orb_v2_strategy.py`

## High-Value Research Sources
- `trading_os/docs/ORB_TRADER_METHODOLOGIES_SYNTHESIS.md`
- `trading_os/docs/V2_SPECIFICATION_EVIDENCE_BASED.md`
- `strat/research_texts/RP_Profit_8am_ORB_Research_Dossier.md`
- `strat/research_texts/Indicator_Visual_Research_Source_Pack.md`
- `strat/research_texts/Trading_Strategy_V1_Restart_Brief.md`
- `strat/research_texts/Mason_Module_ORB_Retest_System_v1.md`

## Pine/Execution References
- `trading_os/pine/ORB_V2_DECISION_DASHBOARD.pine`
- `trading_os/pine/ORB_Strategy_v1_0_COMPLETE.pine`
- `ES_ORB_Strategy_v1_1_FIXED.txt`
- `ES_ORB_Indicator_v1_1_FIXED.txt`

## Legacy Working-Strategy Artifacts To Mine
- `strat/Trade Stratagey/pre built orb strat.txt`
- `strat/Trade Stratagey/perp orb.txt`
- `strat/Trade Stratagey/ML_R1.2_Adaptive_2nd_Trade_CME_MINI_MES1!_2026-03-23.xlsx`
- `strat/Trade Stratagey/ML_R1.3_ORB_Retest_+_Confluence_CME_MINI_MES1!_2026-03-21.xlsx`
- `strat/Trade Stratagey/V6_ORB_Midpoint_Continuation_CME_MINI_ES1!_2026-03-23.xlsx`

## Component Mapping Into Code
- ORB structure/window/range: implemented and tunable.
- EMA/VWAP/volume/displacement filters: implemented and tunable.
- ICT proxies (MSS/FVG/rejection/engulfing): implemented as toggles.
- Short-side and break-even: implemented.
- Funded constraints + walk-forward: implemented.

## Gaps To Close Next
- Promote hidden rules from legacy assets into explicit parameters.
- Enforce one-trade-per-day mode as a hard switch in optimizer.
- Add strict cadence objective profile (`monthly_pass_rate` weighted first).
- Add side-specific confluence thresholds (long and short separate).
- Add controlled 2-trades/day profile with risk cap (for frequency unlock).

## Immediate Mining Workflow
1. Extract rules from each legacy strategy artifact into a structured checklist.
2. Tag each rule as: implemented, partial, missing.
3. Convert missing rules into optimizer parameters or binary toggles.
4. Run attribution tests one rule at a time before combined sweeps.

## User-Locked Funded Profile (2026-07-03)
- Primary strategy references: `strat/STRATEGY_SOURCE_OF_TRUTH.md`, `strat/MASTER_TRADING_SYSTEM.md`, `strat/ES_ORB_Strategy_v1.0.txt`.
- Supporting context only: `strat/BACKTEST_COMPARISON.csv`, `strat/EDGE_ATTRIBUTION.md`, `strat/PHASE7_TEST_PLAN.md`, `strat/AUDIT_CURRENT_STATE.md`, `strat/TRADE_SCREENSHOT_ANALYSIS.md`.
- Focus model: selective liquidity sweep + reclaim/rejection with VWAP/EMA confirmation.
- Avoid old/simple ORB breakout optimization except explicit baseline comparison.
- Funded constraints: 50k, 3k target, 2k daily loss, trailing DD survival priority.
- Risk preference: primary strict 1 trade/day, 9:30-11:00 window, preferred 10:30 cutoff, strategy daily stop around $200.
- Secondary model: max 2 trades/day only if first trade loses, with full confluence and no late/revenge entries.
