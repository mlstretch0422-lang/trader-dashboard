# Pine Code Audit — ES/MES ORB v1.1

Files reviewed:

- `ES_ORB_Indicator_v1_1_FIXED.txt`
- `ES_ORB_Strategy_v1_1_FIXED.txt`

Status: **research code, not production validated**.

## Critical findings

### 1. Force-flat time test is structurally broken

The strategy calls:

```pine
f_inWindow(i_flatTime, i_flatTime == "2359" ? "0000" : i_flatTime)
```

For the default `1100`, start and end are equal. The helper's equal/overnight branch becomes:

```pine
curMins >= startMins or curMins < endMins
```

When start and end are the same, that expression is effectively true for every minute. The later edge detector therefore does not create a reliable 11:00 force-flat event.

**Impact:** the code claims hard flat at 11:00, but the implementation does not reliably enforce it.

**Required fix:** use a dedicated at-or-after-time transition:

```pine
pastFlat = curMins >= flatMins
forceFlatHit = pastFlat and not pastFlat[1]
```

### 2. Boundary retest can be counted on the breakout bar

After a breakout arms `setupDir`, the script immediately checks:

```pine
if setupDir == 1 and not retestSeen and low <= longRetestLevel
    retestSeen := true
```

For boundary mode, the breakout candle's own low can be at or below the ORB boundary. Because the retest check runs later on the same bar, the breakout candle can count as its own retest.

**Impact:** `Boundary` may collapse toward immediate-breakout behavior and contaminate attribution.

**Required fix:** require `bar_index > setupBar` for non-breakout retest modes.

### 3. Retest setups do not have a clear structural invalidation

A long setup can sweep deeply below the ORB, remain armed, and later trigger if price closes back above the ORB high. The current timeout is the main reset mechanism.

**Impact:** the strategy can classify a failed setup and a later fresh move as one continuous setup.

**Required fix:** declare invalidation explicitly, such as:

- long setup resets after an accepted close below ORB low
- short setup resets after an accepted close above ORB high

The exact invalidation is a research parameter and must be logged.

### 4. New-entry cutoff conflicts with the primary operating rule

The strategy default is:

```pine
i_tradeEnd = "1100"
```

The current primary research model states no new entries after 10:30 and force-flat by 11:00.

**Impact:** the code can authorize entries during the final 30 minutes that the current operating plan intends to block.

**Required fix:** use 10:30 as the primary default while keeping the value configurable for attribution tests.

### 5. Same-bar staircase movement creates intrabar ambiguity

The strategy raises `liveStop` when the bar's high/low reaches TP levels, then submits exits using the updated stop. On a bar that touches both the original stop and a target, OHLC data may not establish which event happened first.

**Impact:** historical results may benefit from optimistic event ordering, especially without lower-timeframe bar magnifier data.

**Required fix:** isolate entry logic with a single target and fixed stop first. Test staircase and partial exits later with explicit intrabar assumptions.

## Important research limitations

### 6. Multiple components change together

The v1.1 strategy combines:

- ORB clock
- retest mode
- displacement gate
- VWAP
- optional EMA
- ORB range gate
- stop method
- three targets
- staircase stop

A positive backtest does not identify which component helped or hurt.

### 7. `FIXED` is a version label only

The file name does not mean:

- profitable
- robust
- walk-forward validated
- paper-forward validated
- safe for live use

### 8. The cost model is easy to misread

The declaration includes:

```pine
commission_type=strategy.commission.cash_per_contract
commission_value=1.2
slippage=2
```

In TradingView Pine, `commission_value=1.2` under `cash_per_contract` means **$1.20 per contract per executed order** in the strategy account currency. More importantly, `slippage=2` means **2 ticks**, not 2 index points.

For ES/MES, where the minimum tick is typically 0.25 index points, `slippage=2` models about **0.50 points of slippage per affected fill**, not 2.00 points. Any project document or old test note describing this declaration as “2 points slippage” is therefore inconsistent with the Pine implementation.

**Impact:** comparing runs while describing one as 2-point slippage and another as `slippage=2` can create false apples-to-apples claims.

**Required fix:** every exported run must record both the raw Pine setting and its interpreted units, e.g. `slippage_ticks=2`, `mintick=0.25`, `slippage_points=0.50`.

### 9. `process_orders_on_close=true` is a deliberate fill assumption, not live execution proof

The strategy declaration enables:

```pine
process_orders_on_close=true
```

TradingView's broker emulator can therefore fill generated orders on the signal bar's closing tick rather than waiting for the next bar's open. This keeps signal-close entries aligned with the coded `plannedEntry := close`, but it can be more optimistic than live execution in some situations.

**Impact:** a profitable close-fill backtest does not establish that the same result survives next-tick or real broker fills.

**Required fix:** keep the setting frozen during component attribution, label the result as a close-fill historical model, then run a separate execution-sensitivity test before production promotion.

### 10. Range thresholds are instrument/regime assumptions

The default 5–50 point ORB gate is coded identically for ES and MES because both quote the same index points, but its volatility-regime effect is not established.

### 11. Indicator and strategy authorization differ

The indicator emits visual signals; the strategy simulates orders and management. A chart signal compiling successfully does not validate fill quality or account survival.

## Required remediation order

1. Fix force-flat logic.
2. Prevent same-bar retests except in explicit breakout mode.
3. Add setup invalidation and reset reason.
4. Change primary new-entry cutoff to 10:30.
5. Create a clean one-entry / one-stop / one-target attribution baseline.
6. Lock and record the exact date range and execution model.
7. Reproduce a known historical export.
8. Test entry mode, ORB clock, VWAP, EMA, displacement, and range filters one at a time.
9. Add partials, staircase stops, breakeven, and adaptive logic only after the entry model is stable.

## Promotion decision

`ES_ORB_Strategy_v1_1_FIXED.txt` remains **TESTING / IMPLEMENTED**. It should not be the production strategy or the source of premium performance claims until the critical timing and retest issues are fixed and the resulting model is validated.
