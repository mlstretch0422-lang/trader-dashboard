# PHASE 7 TEST PLAN

This plan turns the research findings into a prioritized set of experiments. The goal is to validate the real edge components and reject the ones that do not improve performance.

## Evidence-based test hierarchy

1. Baseline strategy: `midpoint retest` with clean ORB structure and no optional confirmation filters.
2. Core edge validation: compare `raw ORB only` vs `ORB + retest`.
3. Confirmation tests: evaluate `VWAP` and `EMA` as independent confirmation layers.
4. Session/timing tests: reconcile `8:00–8:15 ORB` structure with `9:30` market open execution.
5. Regime filter tests: validate `ATR` / oversized range skip.
6. Risk/management tests: define `stop loss` and `take profit` structure with direct measurement.
7. Reject hypotheses: test `adaptive sizing / second trade / pyramiding / scaling` as likely distractions.

## Prioritized hypotheses

### 1. Midpoint retest is baseline (PROVEN)
- Keep this as the reference execution model.
- Do not remove it until a stronger counterexample appears.

### 2. Raw ORB-only execution is likely harmful
- Test: baseline vs same ORB logic without a retest trigger.
- Primary metrics: profit factor, expectancy/trade.
- Secondary metrics: drawdown, win rate, trade count.
- Invalidation: raw ORB-only underperforms baseline, especially if PF <= 1.05 or expectancy <= 0.

### 3. VWAP confirmation
- Test: baseline + VWAP alignment vs baseline alone.
- Keep other layers constant.
- Reject if it reduces trade quality without raising expectancy or PF.

### 4. EMA trend alignment
- Test: baseline + EMA bias vs baseline alone.
- Prefer a simple trend direction rule over a complex mashup.

### 5. Session/time filtering
- Test whether the entry and management rules should be confined to:
  - 8:00–8:15 ORB structure only
  - 9:30–10:30 execution window only
  - ORB structure plus a 9:30 execution overlay
- Use the same history for all variants.

### 6. ATR / volatility regime skip
- Test: skip oversized ORBs or use ATR-based regime thresholds.
- Reject if it throws away too many trades without improving PF/expectancy.

### 7. Stop loss and take profit structure
- Test a simple ORB boundary stop vs a fixed distance stop.
- Test TP splits under the same entry model.
- Focus on metrics, not on arbitrary target ratios.

### 8. Adaptive / second trade / pyramiding / scaling
- Test as negative hypotheses. Compare baseline to variants that add:
  - a second trade after an initial loss
  - pyramiding into a winning move
  - dynamic sizing
- Reject unless they raise profit factor and expectancy while preserving drawdown.

## Data requirements

- Minimum sample target: 200 trades or 6 months of suitable data.
- If paper trading data is limited, use it as qualitative validation and rely on backtest history for statistical tests.
- Use the new paper trading order reconstruction pipeline to verify real execution and note any dataset gaps.

## Practical acceptance criteria

- Accept a component if it improves profit factor and expectancy while keeping drawdown stable or lower.
- Reject a component if PF <= 1.05, expectancy <= 0, or if the improvement comes from a dramatically smaller sample.
- Prefer components that have a clear, testable job: bias, confirmation, setup quality, timing, or risk management.

## Notes for the next phase

- The current research attribution says the edge is in `midpoint retest + context`, not in raw ORB size or timing alone.
- The test plan should focus on isolating that edge before tuning peripheral filters.
- Use the paper trading file pipeline to link actual order fills to trade types once the data schema is stable.

