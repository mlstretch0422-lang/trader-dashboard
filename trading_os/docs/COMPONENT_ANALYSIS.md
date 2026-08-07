# Component Analysis & Evidence Assessment

**Date**: 2026-06-30  
**Status**: Interim (pending OHLC validation)

---

## Scoring Methodology

For each component, we assess:
- **Evidence Value**: How much data supports this rule?
- **Testability**: Can we isolate this component's impact?
- **Current Status**: Enabled, disabled, or under review?
- **Impact**: Estimated contribution to profitability.

---

## Component 1: ORB Window (08:00–08:15 ET)

**Current Rule**: 
- Build ORB over 15 minutes at market open.
- Freeze at 08:15 ET; no updates.

**Evidence**:
- Mentioned in strategy files as primary setup.
- Reconstructed trades show entries mostly 08:30–10:00 ET (after ORB freeze).
- No data comparing 08:00–08:15 vs. other windows (e.g., 09:30–09:45 post-official market open).

**Testability**: High (can test multiple windows with clean_orb.py).

**Status**: Assumed canonical but unvalidated.

**Recommendation**: Once OHLC is available, test alternate windows:
- 08:00–08:15 (current)
- 09:30–09:45 (post-market-open)
- 09:30–09:45 (RTH official open)

---

## Component 2: Breakout Trigger (vs. Retest Requirement)

**Current Rule** (V1.0): 
- Enter immediately on close beyond ORB edge (breakout).
- **Alternative tested**: Retest to midpoint first, then breakout from midpoint.

**Preliminary Evidence** (CONFIDENCE: **HYPOTHESIS** — needs validation):
- Reconstructed trades labeled "break": 33 trades, PF=2.03, net=$2,717.50, expectancy=$82.35
- Reconstructed trades labeled "retest": 5 trades, PF=0.15, net=-$336.25, expectancy=-$67.25
- **Apparent contradiction**: Documentation emphasizes retest; data suggests breakout performs better.

**Caveats**:
- Retest sample size (N=5) is too small for statistical significance
- Trade labels are heuristic-based (entry_type starting with "Limit"), not validated against actual price action
- Breakout labels could be biased if they capture different volatility regimes
- Documentation may be based on different time periods; market conditions could have changed

**Testability**: Medium (requires OHLC to re-tag as true breakout vs. true retest using actual price levels).

**Status**: **HYPOTHESIS** — Needs validation with OHLC re-tagging and larger sample (200+ trades).

**Action**: Once OHLC available, compute true ORB levels and re-tag each trade's actual entry type. This will upgrade confidence to Medium or High.

---

## Component 3: Entry Stop-Loss Placement

**Current Rule** (V1.0):
- Long: Stop at ORB_LOW.
- Short: Stop at ORB_HIGH.
- **Alternative**: Tighter stop at ORB_MID or dynamic ATR-based stop.

**Preliminary Evidence** (CONFIDENCE: **HYPOTHESIS** — needs investigation):
- Exit type breakdown:
  - Limit/Market exits (N=15): PF~14, net=$4,545, expectancy=$303/trade
  - Stop-loss exits (N=22): PF=0.07, net=-$2,639, expectancy=-$119.94/trade
- **Apparent problem**: Stop-loss exits generate large losses; Limit/Market exits are profitable.

**Possible Explanations** (not mutually exclusive):
1. SL placement is too tight (ORB_LOW/HIGH may not be appropriate)
2. Entry type bias: Certain setups (breakout vs. retest) may cluster in Stop exits
3. Exit classification is incorrect in the data (may be labeled "Stop" but should be "Limit")
4. Sample bias: 22 trades is enough to show a trend, but not enough to conclude causation
5. Market regime: Period may have been favorable to Limit/Market strategies and unfavorable to Stop strategies

**Testability**: High (can test SL placement variants; needs OHLC to verify exit classification).

**Status**: **HYPOTHESIS** — Suggests SL placement warrants investigation, but correlation ≠ causation.

**Action**: 
1. Obtain OHLC and verify exit classifications are correct
2. Run test_sl_alternatives.py to compare 6 SL variants
3. Measure if SL_MID, SL_FIXED_5PTS, or SL_ATR variants improve expectancy

**Expected outcome if true**: +$100–150/trade improvement. If false: stop placement not the issue; problem lies elsewhere.

---

## Component 4: Take-Profit Targets

**Current Rule** (V1.0):
- TP1: 1R (50% qty)
- TP2: 2R (30% qty)
- TP3: 3R (20% qty)
- Staircase stop: move stop to breakeven at TP1, etc.

**Evidence**:
- Reconstructed trades do not clearly separate TP levels in data; need OHLC to measure per-level fills.
- Limit/Market exits (which may include TP fills) show positive expectancy, suggesting TP structure is sound.

**Testability**: Medium (requires OHLC to categorize exits as TP1, TP2, TP3, or SL).

**Status**: Assumed acceptable; pending validation.

**Impact**: Medium — TP structure is likely not the problem; SL is.

---

## Component 5: VWAP Filter (Default: Enabled)

**Current Rule** (V1.0):
- Long entries only above VWAP.
- Short entries only below VWAP.

**Evidence**:
- Reconstructed trades do not label which trades met/missed VWAP alignment.
- No direct measurement of filter contribution.

**Testability**: Medium (can compute VWAP from OHLC sample and re-label entries).

**Status**: Enabled by default but unvalidated.

**Recommendation**: Once OHLC is available, group trades:
- Entries above VWAP (long) or below VWAP (short).
- Entries below VWAP (long) or above VWAP (short).
- Measure PF delta.

---

## Component 6: EMA(50) Filter (Default: Disabled)

**Current Rule** (V1.0):
- Optional; long only above EMA(50), short only below EMA(50).
- Not enabled by default.

**Evidence**:
- No data; not mentioned in reconstructed trades.

**Testability**: Medium (can compute EMA from OHLC and simulate impact).

**Status**: Disabled; recommend testing in V1.1.

**Impact**: Unknown (likely low based on strategy documentation priority).

---

## Component 7: One-Trade-Per-Day Rule

**Current Rule** (V1.0):
- Only one live trade per calendar day.
- If exited, no re-entry same day.
- Reset at market open 08:00 ET.

**Evidence**:
- Reconstructed trades: 17 days of data, but 11 days show multiple trades.
  - 6 days: 1 trade each.
  - 7 days: 2 trades each.
  - 2 days: 3 trades each.
  - 1 day: 4 trades.
  - 1 day: 8 trades.
- **Finding**: Rule not enforced in paper trading data.

**Testability**: High (can simulate enforcement on reconstructed trades).

**Status**: Documented but not enforced in historical data. **Action needed**: Clarify intent and measure impact if enforced.

**Recommendation**: If enforced, simulate by:
- Keeping only first trade each day (if tradeTakenToday=True).
- Measure total trades, net P&L, and PF change.
- Likely result: fewer trades, potentially lower overall P&L but better risk management.

---

## Component 8: No-Trade Conditions (ORB Range Filters)

**Current Rule** (V1.0):
- Skip trading if ORB range < 5 points (too choppy).
- Skip trading if ORB range > 50 points (too volatile).

**Evidence**:
- Reconstructed trades do not include ORB range calculations.
- No data on how often range violates these thresholds.

**Testability**: High (can compute ORB range from OHLC sample).

**Status**: Documented but unvalidated.

**Recommendation**: Once OHLC is available:
- Compute ORB range for all 11 sample days.
- Identify days outside 5–50 range.
- Measure skipped days vs. actual trade performance.

---

## Component 9: Entry Window (08:15–11:00 ET)

**Current Rule** (V1.0):
- Close entry window at 11:00 ET.
- No new entries after 11:00 ET.
- Force flat any open positions at 11:00 ET.

**Evidence**:
- Reconstructed trades show entries up to ~10:00 ET; few entries after 10:00 ET.
- No analysis of how late-window entries perform vs. early-window.

**Testability**: High (can group by entry hour and measure PF by hour).

**Status**: Documented but not validated by hour.

**Recommendation**: Once OHLC is available, group trades by entry hour (09:00, 09:30, 10:00, 10:30) and measure:
- PF by hour.
- Win rate by hour.
- Expected value by hour.
- Identify if certain hours underperform; consider earlier close.

---

## Component 10: Session Hours (08:00–11:00 ET)

**Current Rule** (V1.0):
- Trading window: 08:00 ET (ORB start) to 11:00 ET (forced close).

**Evidence**:
- Matches documented strategy.
- No data on trading outside this window (e.g., 11:00–15:00 ET).

**Testability**: Medium (would require separate backtest setup).

**Status**: Documented but alternative windows not tested.

**Recommendation**: Future research — test extended windows (e.g., 11:00–15:00, full day).

---

## Summary: Component Priority & Action Items

| Component | Priority | Confidence | Status | Action | Expected Impact |
|-----------|----------|-----------|--------|--------|-----------------|
| Breakout (vs. Retest) | **CRITICAL** | **HYPOTHESIS** | Contradiction found in labels | Re-tag with OHLC; validate true entry type | +$82/trade if true |
| Stop-Loss Placement | **CRITICAL** | **HYPOTHESIS** | Underperforming in sample | Test 6 alternatives (SL_MID, ATR, etc.) | +$127/trade if true |
| One-Trade-Per-Day | **HIGH** | **HYPOTHESIS** | Not enforced in data | Clarify intent; measure enforcement impact | Unknown |
| ORB Window (08:00–08:15) | **HIGH** | **UNVALIDATED** | Assumed correct | Test 09:30–09:45 window as alternative | TBD |
| VWAP Filter | **MEDIUM** | **UNVALIDATED** | Enabled but unvalidated | Measure contribution via OHLC | TBD |
| Entry Window (08:15–11:00) | **MEDIUM** | **PARTIALLY VALIDATED** | Some hour analysis done | Group by hour; identify weak hours | TBD |
| TP Targets (1R/2R/3R) | **MEDIUM** | **ASSUMED SOUND** | Not directly tested | Validate with OHLC re-tagging | TBD |
| EMA(50) Filter | **LOW** | **UNVALIDATED** | Disabled | Test in V1.1 | Likely <5% |
| ORB Range Filters (5–50 pts) | **LOW** | **UNVALIDATED** | Unvalidated | Count skipped days; measure impact | TBD |
| Other HTF/Bias | **LOW** | **RESEARCH ONLY** | Requires manual work | Defer; manual annotations needed | TBD |

---

## Next Steps (In Priority Order)

### Phase 1: Obtain & Validate OHLC
1. Obtain ES/MES 1-minute OHLC covering 2026-03-19 to 2026-04-21 (reconstructed trade date range).
2. Re-run `re_tag_trades_with_ohlc.py` to compute true entry types (breakout vs. retest).
3. Compute ORB range, VWAP, EMA for all days.
4. Re-tag all exits as TP1, TP2, TP3, or SL.

### Phase 2: Validate Core Components
5. Run component tests (OHLC-dependent):
   - Breakout vs. Retest: confirm PF difference.
   - VWAP filter contribution: on/off comparison.
   - One-trade-per-day impact: enforced vs. unforced.
   - Entry hour performance: group by hour, rank by expectancy.

### Phase 3: Test Stop-Loss Alternatives
6. Create alternate SL placement tests:
   - SL at ORB_MID (tighter).
   - SL at ORB_EDGE - 5 pts (wider).
   - SL at Entry - 1 ATR (dynamic).
   - Time-based SL (e.g., exit after 30 min if not TP'd).
7. Measure PF, expectancy, and win rate for each variant.

### Phase 4: Finalize & Translate
8. Once Phase 2 validation is complete, confirm V1.0 rules and finalize MASTER_DOCUMENT.
9. Translate clean_orb.py logic to Pine Script v6 (indicator and strategy).
10. Backtest Pine code on TradingView against reconstructed trades.
11. Prepare community/Discord documentation.

---

**Approval**: Pending Phase 1 & 2 completion.
