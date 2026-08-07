# PHASE 7 TEST PLAN

This plan converts the repository's mixed strategy claims into controlled experiments. The goal is to identify which components improve performance and drawdown behavior without treating a complete historical configuration as proof of every rule inside it.

## Current evidence baseline

The available comparison file contains four historical exports:

| Configuration | Instrument / TF | Trades | Win rate | PF | Max DD | Expectancy | Research decision |
|---|---|---:|---:|---:|---:|---:|---|
| V6 ORB Midpoint Continuation | ES / 15m | 156 | 39.1% | 1.431 | $8,875 / 17.75% | $209.94 | Keep as reference configuration; not isolated proof |
| V6 duplicate export | ES / 15m | 156 | 39.1% | 1.428 | $9,075 / 18.15% | $208.97 | Investigate reproduction difference |
| ML R1.3 ORB Retest + Confluence | MES / 5m | 74 | 40.54% | 1.284 | $368.75 / 0.74% | $7.38 | Promising but below sample target |
| ML R1.2 Adaptive Second Trade | MES / 15m | 82 | 43.9% | 0.949 | $1,481.25 / 2.96% | -$2.48 | Negative evidence for this implementation |

Source: `strat/BACKTEST_COMPARISON.csv`.

The comparison is not apples-to-apples. Instruments, timeframes, date ranges, strategy versions, sizing, and potentially cost assumptions differ. These rows define starting evidence, not final winners.

## Evidence-based test hierarchy

1. **Reproduce one baseline exactly.** Confirm that the code, data, settings, sizing, commission, and slippage recreate the recorded output.
2. **Entry-mode attribution.** Compare immediate breakout, ORB boundary retest, and ORB midpoint retest with every other variable locked.
3. **ORB-clock reconciliation.** Compare 08:00–08:15, 09:30–09:45, and 09:30–10:00 on the same history.
4. **Core filter attribution.** Test VWAP, EMA, displacement, and ORB-range gates one at a time.
5. **Mechanical discretionary translation.** Define and test liquidity sweep → reclaim/rejection → confirmation.
6. **Risk and management attribution.** Compare stop, target, breakeven, partials, and time exits only after entry logic is stable.
7. **Negative-hypothesis tests.** Re-test second trade, adaptive sizing, pyramiding, and scaling only against an identical fixed baseline.
8. **Walk-forward and paper-forward validation.** No promotion before chronological holdout and execution confirmation.

## Test 0 — Baseline reproduction

### Purpose
Prove that the research pipeline can reproduce a known historical result before changing logic.

### Preferred starting candidate
Use the V6 midpoint export because it has the largest available sample: 156 trades.

### Required metadata

- exact Pine file and commit
- symbol and contract mapping
- chart timeframe
- ORB clock
- session timezone
- entry and exit settings
- quantity and point value
- commission
- slippage
- date range
- bar magnifier / intrabar assumptions
- strategy properties

### Pass condition

The reproduced trade count and core metrics should match the export within documented tolerances. The two existing V6 rows differ slightly despite reporting the same date range and trade count, so the discrepancy must be explained rather than ignored.

## Test 1 — Entry-mode attribution

### Hypothesis
A retest requirement improves expectancy and drawdown behavior versus immediate ORB breakout entry.

### Variants

- A: immediate breakout
- B: boundary retest
- C: midpoint retest

### Locked variables

- same instrument
- same timeframe
- same ORB clock
- same date range
- same context filters
- same stop and target
- same quantity
- same costs
- same one-trade-per-day rule

### Primary metrics

- profit factor
- expectancy per trade
- max drawdown
- worst losing sequence
- trade count

### Decision rule

Midpoint remains the reference configuration only if it improves expectancy or drawdown without relying on a dramatically smaller sample. Until this test is complete, midpoint is **SUPPORTED BASELINE / TESTING**, not proven.

## Test 2 — ORB-clock reconciliation

### Conflict being resolved

- current Pine and all rows in `BACKTEST_COMPARISON.csv`: 08:00–08:15
- `STRATEGY_SOURCE_OF_TRUTH.md`: 09:30–09:45 primary, 09:30–10:00 alternate

### Variants

- A: 08:00–08:15 reference range, 09:30 execution overlay
- B: 09:30–09:45 cash-open ORB
- C: 09:30–10:00 extended cash-open ORB

### Decision rule

No clock is promoted because it is called “industry standard,” appears in current code, or was used in an older profitable run. Select only after same-model comparison and holdout validation.

## Test 3 — VWAP attribution

### Variants

- baseline without VWAP requirement
- baseline with directional VWAP alignment

### Decision rule

Keep VWAP only if it improves expectancy or drawdown stability after accounting for reduced trade count. Claims such as “adds 3–5% edge” remain unsupported until a result file proves them.

## Test 4 — EMA attribution

### Variants

- baseline without EMA
- baseline with one fixed EMA rule

### Restrictions

Do not optimize many EMA lengths in the first test. Choose one documented length, run the comparison, and treat further length search as a separate sensitivity study.

## Test 5 — Displacement attribution

### Current implementation

A breakout candle passes if either:

- body is at least 35% of ORB range, or
- body is at least 0.75 × ATR(14)

### Variants

- no displacement gate
- ORB-body gate only
- ATR gate only
- current OR condition

### Follow-up sensitivity

Only after the basic comparison, test a small pre-declared grid. Do not optimize dozens of thresholds on the full history.

## Test 6 — ORB-range / volatility gate

### Current implementation

The Pine files use a 5–50 point ORB range gate.

### Required work

- confirm whether the point thresholds are intended for ES, MES, or both
- bucket results by ORB range
- compare no gate versus the current gate
- compare fixed points versus normalized ATR/range percentiles

### Decision rule

Reject thresholds that merely delete losing periods in-sample without stable holdout behavior.

## Test 7 — Liquidity sweep → reclaim/rejection

### Purpose
Translate Mason's preferred discretionary sequence into objective states.

### Minimum mechanical definition

1. price trades beyond a mapped liquidity level by a declared minimum amount
2. price closes back through the level within a declared timeout
3. bearish or bullish continuation fails according to an objective rule
4. short-term structure reasserts in the allowed direction
5. entry, invalidation, and target are known before authorization

### Required controls

- breakout-retest baseline
- sweep without reclaim
- sweep + reclaim
- sweep + reclaim + one confirmation layer

No wick shape, engulfing pattern, FVG, VWAP, EMA, or volume rule becomes mandatory unless tested independently.

## Test 8 — Stops and targets

Run only after the entry model is frozen.

### Stop variants

- opposite ORB boundary
- midpoint / structure stop
- fixed-point stop

### Exit variants

- fixed R target
- liquidity target
- partial exits
- breakeven
- hard time exit

Each management test must use the same entry stream. Otherwise entry and exit effects cannot be separated.

## Test 9 — Second trade and adaptive complexity

### Existing evidence

The available ML R1.2 adaptive-second-trade run reports:

- 82 trades
- -$203.75 net
- PF 0.949
- expectancy -$2.48
- max drawdown $1,481.25 / 2.96%

This is negative evidence for that tested version.

### Re-test rule

Do not spend additional development time on second trades, pyramiding, or adaptive sizing until the one-trade fixed-size baseline is reproduced and stable. Any future variant must beat the identical baseline on expectancy and drawdown, not merely net profit.

## Data requirements

### Minimum research target

- 200 trades when feasible
- at least 6 months covering multiple volatility regimes
- chronological train / validation / final holdout
- realistic commission and slippage
- no lookahead
- no silent parameter changes between variants

### Required outputs per run

- configuration manifest
- trade log
- daily PnL
- equity curve
- drawdown curve
- monthly breakdown
- losing-sequence report
- source commit
- acceptance decision

## Acceptance criteria

A component may move from `TESTING` to accepted only when:

1. its exact job is defined
2. the comparison isolates that component
3. costs and fills are documented
4. sample size and date range are visible
5. improvement is not caused only by deleting most trades
6. drawdown does not materially worsen
7. chronological holdout remains acceptable
8. replay or paper-forward behavior matches the mechanical definition

## Rejection criteria

Reject or retire a component when:

- PF is at or below 1.05 with non-positive expectancy
- drawdown worsens without a compensating and robust expectancy gain
- performance depends on one narrow period or parameter value
- the test cannot be reproduced
- the rule is subjective or cannot be coded without hindsight

## Immediate execution order

1. Reproduce V6 midpoint result.
2. Resolve the duplicate-export discrepancy.
3. Run entry-mode attribution.
4. Run ORB-clock comparison.
5. Run VWAP and EMA attribution.
6. Run displacement and range-gate attribution.
7. Build the first mechanical sweep/reclaim prototype.
8. Walk-forward the surviving model.
9. Paper-forward the exact frozen rules.

The purpose of Phase 7 is not to produce a prettier backtest. It is to earn each rule separately and leave a permanent evidence trail in the repository.
