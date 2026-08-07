# Content Status Audit

This audit separates accepted operating constraints, implemented logic, historical configuration evidence, untested hypotheses, and retired ideas.

## Status definitions

- **VERIFIED** — accepted project rule or governance requirement. This does not automatically mean statistically proven edge.
- **TESTING** — implemented or historically exercised, but not proven enough to present as settled.
- **UNTESTED** — idea, toggle, or confluence without an accepted comparison record.
- **RETIRED** — rejected, deprecated, or excluded from active logic.

## Evidence levels

1. `PROJECT_RULE`
2. `IMPLEMENTED`
3. `BACKTESTED`
4. `ISOLATED_ATTRIBUTION`
5. `WALK_FORWARD`
6. `PAPER_FORWARD`
7. `LIVE`

A higher evidence label is not inferred automatically. Every promotion needs a named result file and acceptance decision.

## VERIFIED operating constraints

| Item | Status basis |
|---|---|
| Primary market is MES / ES | Repeated throughout the project files and Pine scripts. |
| New-entry window stops no later than 10:30 for the primary model | Explicitly documented in the mechanical research brief. |
| Force-flat by 11:00 is part of the primary operating model | Explicitly documented in the mechanical research brief. |
| Maximum one planned trade per day is the primary model | Explicitly documented in the mechanical research brief. |
| The system must be evaluated as bias → setup → trigger → risk → execution → validation | Explicit architecture in the mechanical research brief. |
| Backtests must avoid lookahead bias and unrealistic fills | Explicit validation requirement. |
| Historical, replay, paper, funded-evaluation, and live performance remain separate | Project governance requirement. |

These are verified as project constraints or process rules. They are not automatically edge claims.

## Active conflicts that block promotion

### ORB clock

The repository does not have one uncontested ORB clock:

- current Pine files: 08:00–08:15 New York
- all four rows in `strat/BACKTEST_COMPARISON.csv`: 08:00–08:15
- `strat/STRATEGY_SOURCE_OF_TRUTH.md`: 09:30–09:45 primary, 09:30–10:00 alternate
- `strat/AUDIT_CURRENT_STATE.md`: documents the conflict directly

**Classification:** TESTING / BACKTESTED.

No clock is presented as settled until the variants are compared with the same instrument, timeframe, date range, sizing, and cost model.

### Preferred entry model

The current Pine files implement breakout → retest → continuation. The research brief prefers liquidity sweep → reclaim/rejection → continuation. These are related but not identical state machines.

**Classification:** both remain TESTING until they are defined and compared cleanly.

## Historical configuration evidence

Source: `strat/BACKTEST_COMPARISON.csv`.

| Configuration | Instrument / TF | Date range | Trades | Win rate | PF | Max DD | Expectancy | Decision |
|---|---|---|---:|---:|---:|---:|---:|---|
| V6 ORB Midpoint Continuation | ES / 15m | 2025-04-01 to 2026-02-26 | 156 | 39.1% | 1.431 | $8,875 / 17.75% | $209.94 | Research baseline; not production proof |
| V6 duplicate export | ES / 15m | same period | 156 | 39.1% | 1.428 | $9,075 / 18.15% | $208.97 | Reproduction discrepancy |
| ML R1.3 ORB Retest + Confluence | MES / 5m | 2025-12-08 to 2026-03-20 | 74 | 40.54% | 1.284 | $368.75 / 0.74% | $7.38 | Promising but small and non-isolated |
| ML R1.2 Adaptive Second Trade | MES / 15m | 2025-05-01 to 2026-03-20 | 82 | 43.9% | 0.949 | $1,481.25 / 2.96% | -$2.48 | Negative evidence for this variant |

Important limitations:

1. The configurations are not apples-to-apples.
2. Instruments, timeframes, periods, strategy versions, and management differ.
3. The comparison file does not fully document commissions, slippage, or fill assumptions.
4. A positive complete configuration does not prove which internal component caused the result.
5. The two V6 exports differ slightly despite the same period and trade count, so reproduction must be resolved.

## TESTING components

| Item | Current evidence | Why it is not VERIFIED edge |
|---|---|---|
| Breakout → retest → continuation | Implemented and historically backtested | No identical raw-breakout control or holdout |
| Midpoint retest | Current Pine default; positive V6 historical exports | Not isolated against boundary retest and immediate breakout |
| VWAP directional alignment | Implemented | No accepted off/on attribution record |
| 35% ORB-body or 0.75× ATR displacement gate | Implemented | Threshold effect not isolated or sensitivity-tested |
| 5–50 point ORB range gate | Implemented | Instrument and regime suitability not established |
| Liquidity sweep → reclaim/rejection model | Preferred research direction | Mechanical definition and test output not yet accepted |
| Second trade after loss | Historical adaptive variant exists | Available variant has negative expectancy and PF below 1 |
| Trailing-drawdown survival ranking | Correct evaluation priority | Candidate results still need actual walk-forward evidence |

## UNTESTED components

The following remain outside the active Trade Bible unless a separate accepted test record supports them:

- EMA alignment as a required rule
- volume confirmation
- red-news proximity implementation
- FVG requirement
- London level requirement
- premarket level requirement beyond the selected ORB structure
- previous-day direction filter
- previous-day high/low/close as mandatory setup levels
- engulfing-candle requirement
- rejection-wick requirement as a universal trigger
- minimum close-strength thresholds
- breakeven logic
- trailing-stop logic
- partial exits
- adaptive contract scaling
- pyramiding
- any confluence score presented as proven

## RETIRED / excluded from active logic

| Item | Reason |
|---|---|
| Blind ORB breakout entry | An ORB break alone is not sufficient authorization. Keep only as a research control. |
| Vague rules such as “looks bullish,” “momentum seems strong,” or “good-looking setup” | Not mechanical or testable. |
| Ranking candidates by net profit alone | Explicitly rejected by the research framework. |
| Presenting low-sample optimizer winners as production-ready | Fails evidence and robustness standards. |
| Combining backtest, paper, funded, and live metrics | Misleading and prohibited by governance. |

## Code audit: `ES_ORB_Indicator_v1_1_FIXED.txt`

### What the script currently does

- Builds an 08:00–08:15 New York ORB.
- Allows a 09:30–11:00 trade-seeking window.
- Applies ORB-range, displacement, VWAP, and optional EMA gates.
- Arms long or short after a close beyond the ORB.
- Waits for breakout, boundary, or midpoint retest mode.
- Emits at most one signal per day.
- Displays ORB levels and a dashboard.

### Important limitations

1. `FIXED` is a code-version label, not validation evidence.
2. The indicator's trade window currently extends to 11:00, while the primary research model says no new entries after 10:30 and force-flat by 11:00.
3. The script models breakout-retest continuation, not the full preferred liquidity-sweep sequence.
4. VWAP, EMA, displacement, range, and timeout defaults are research parameters.
5. The indicator does not establish realistic fills, costs, drawdown survival, or out-of-sample robustness.
6. A TradingView signal stays labeled as research until strategy tests and replay/paper evidence support promotion.

## Website rules

- VERIFIED project constraints may appear as operating rules, with wording that does not imply statistical edge.
- TESTING items display a visible `Testing` badge and evidence link.
- UNTESTED items belong in the Research Vault / experiment queue.
- RETIRED items belong in version history or control-test documentation.
- Every performance metric states source, sample size, date range, instrument, timeframe, cost-model status, test type, and decision.
- No indicator or strategy is marketed as validated because it compiles, plots, or has one positive historical run.

## Required evidence before production promotion

1. Reproduce a named baseline exactly.
2. Resolve the duplicate V6 output difference.
3. Isolate midpoint versus boundary versus immediate breakout.
4. Compare ORB clocks under one fixed design.
5. Attribute VWAP, EMA, displacement, and range filters separately.
6. Run chronological walk-forward and final holdout tests.
7. Paper-forward the exact frozen rules.
8. Reconcile the final Pine implementation with Mason's preferred liquidity-sweep decision process.

## Current conclusion

The repository contains useful historical evidence and a promising midpoint/retest research baseline. It does not yet contain enough isolated and out-of-sample evidence to call midpoint, VWAP, EMA, displacement, the ORB clock, or other confluences proven edge.
