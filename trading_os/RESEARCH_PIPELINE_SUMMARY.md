# Research Pipeline Summary — Ready for OHLC Validation

**Date**: 2026-06-30  
**Status**: Documentation complete, awaiting OHLC data for Phase 1 validation

---

## What's Been Completed

### 1. **V1.0 Technical Specification** 
📄 File: [trading_os/docs/V1_SPEC.md](../docs/V1_SPEC.md)

A complete, plain-English specification of the system version 1.0:
- **ORB build**: 08:00–08:15 ET window (15 min)
- **Entry**: Breakout beyond ORB edge (no retest requirement in V1.0)
- **Exit**: SL at ORB edge, TP 1R/2R/3R with staircase stop
- **Filters**: VWAP optional (enabled), EMA disabled
- **One trade per day**: Enforced

This spec is the canonical **source of truth** for all implementation (Python, Pine, execution).

---

### 2. **Master Document** 
📄 File: [trading_os/MASTER_DOCUMENT.md](../MASTER_DOCUMENT.md)

Updated to include:
- **Vision**: Simple, rule-based, data-backed system
- **Canonical rules**: Summarized V1.0
- **Current evidence**: Metrics from 38 reconstructed trades
- **Research status**: High/medium/low priority items
- **Links**: All research docs, code, data sources

---

### 3. **Component Analysis & Evidence Assessment** 
📄 File: [trading_os/docs/COMPONENT_ANALYSIS.md](../docs/COMPONENT_ANALYSIS.md)

Detailed analysis of 10 components:
1. ORB window (08:00–08:15) — unvalidated
2. Breakout trigger — **contradicts documentation** (winning)
3. SL placement — **underperforming** (critical issue)
4. TP targets — assumed sound
5. VWAP filter — enabled but unvalidated
6. EMA filter — disabled
7. One-trade-per-day — not enforced in data
8. Range filters (5–50 pts) — unvalidated
9. Entry window (08:15–11:00) — partially validated
10. Session hours — documented but alternative windows untested

**Priority ranking**: 4 high, 3 medium, 2 low, + future research items.

---

### 4. **Research Summary Generation**
📄 File: [trading_os/experiments/produce_research_summary.py](../experiments/produce_research_summary.py)  
📊 Output: [trading_os/experiments/outputs/trade_research_summary.json](../experiments/outputs/trade_research_summary.json)

Groups 38 reconstructed trades by:
- Trade label (break vs. retest)
- Entry type, exit type, hour, symbol, direction

**Key findings**:
| Grouping | PF | Net P&L | Expectancy |
|----------|----|---------| -----------|
| **Overall** | 1.78 | $2,381 | $62.66 |
| Break entries | 2.03 | $2,718 | +$82 ✓ |
| Retest entries | 0.15 | -$336 | -$67 ✗ |
| Limit/Market exits | ~14 | $4,545 | +$303 ✓✓ |
| Stop-loss exits | 0.07 | -$2,639 | -$120 ✗✗ |

---

### 5. **Stop-Loss Alternative Tester**
📄 File: [trading_os/experiments/test_sl_alternatives.py](../experiments/test_sl_alternatives.py)

Parameterized test suite ready to run on OHLC data:
- `SL_ORB_EDGE` (current)
- `SL_ORB_MID` (tighter)
- `SL_FIXED_5PTS`, `SL_FIXED_10PTS` (fixed)
- `SL_ATR1X`, `SL_ATR2X` (dynamic)

**Usage** (once OHLC available):
```bash
python3 test_sl_alternatives.py \
  --ohlc <ES_1min_ohlc.csv> \
  --trades strat/data/reconstructed_trades_tagged.csv \
  --output outputs/
```

Output: Comparison table ranked by expectancy, JSON results.

---

## Critical Findings (Evidence-Based)

### Finding #1: Breakout Outperforms Retest ⚠️
**Contradiction with documentation**:
- Docs emphasize "midpoint retest" as the proven edge
- Actual data: Breakout entries (PF=2.03) vs. Retest entries (PF=0.15)
- **Ratio**: Breakout is 13.5x better

**Current treatment in V1.0**: Removed retest requirement; using immediate breakout entry.

**Validation needed**: Re-tag trades using OHLC to confirm these are true breakout vs. true retest setups.

### Finding #2: Stop-Loss Exits Are Losing ⚠️⚠️
**Critical problem**:
- Stop-loss exits: -$2,639 net on 22 exits (expectancy -$120/trade)
- Limit/Market exits: +$4,545 net on 15 exits (expectancy +$303/trade)
- **Impact**: Stop exits are a net drag of $427/trade compared to Limit/Market

**Root cause unknown**:
- SL placement too tight (ORB_HIGH/LOW)?
- Exits too early, missing TP targets?
- Slippage on stop fills?

**Solution approach**: Test 6 SL variants (via test_sl_alternatives.py) to find optimal placement.

**Expected outcome**: +$100–150 expectancy/trade improvement.

### Finding #3: One-Trade-Per-Day Not Enforced
**Documentation claim**: "One trade per day maximum"
**Actual data**: 11 of 17 days have 2+ trades; 1 day has 8 trades
**Impact**: Unknown (could be positive or negative)

---

## What We Need to Proceed (CRITICAL BLOCKER)

### OHLC Data Required
We need **ES or MES 1-minute OHLC** covering the **exact dates** of the reconstructed trades:

**Date range**: 2026-03-19 to 2026-04-21 (38 trades across ~17 days)

**Format expected**:
```
datetime,open,high,low,close,volume
2026-03-19 08:00:00,4700.5,4710.0,4695.0,4705.0,15000
2026-03-19 08:01:00,4705.0,4715.0,4700.0,4710.0,12000
...
```

**Where to get it**:
- TradingView (with API or export)
- Broker data export (IB, TD Ameritrade, etc.)
- Free historical data sources (yfinance, etc.)

**Why it's essential**:
1. Re-tag all 38 trades as true breakout vs. true retest
2. Compute ORB range for each day (identify skipped days)
3. Compute VWAP for each trade (measure filter contribution)
4. Re-tag exits as TP1, TP2, TP3, or SL
5. Run stop-loss alternative tests to find optimal placement

---

## Next Steps (Post-OHLC)

### Phase 1: Re-Validation (1–2 hours)
1. Place OHLC CSV in `trading_os/frd_sample_futures_ES/` (or similar)
2. Run `re_tag_trades_with_ohlc.py`:
   ```bash
   python3 re_tag_trades_with_ohlc.py \
     --ohlc <csv> \
     --trades strat/data/reconstructed_trades_tagged.csv \
     --output outputs/
   ```
3. Output: Trades re-tagged with ORB info, entry type, exit type, confidence scores.

### Phase 2: Stop-Loss Testing (30 min)
1. Run `test_sl_alternatives.py` (see above)
2. Output: Comparison table; identify best SL placement
3. Update V1.0 spec with winning SL variant

### Phase 3: Component Contribution Analysis (1–2 hours)
1. Group trades by VWAP alignment (long above, short below)
2. Group by one-trade-per-day (enforced vs. not)
3. Group by entry hour (identify weak hours)
4. Measure PF delta for each filter

### Phase 4: Pine Translation (2–4 hours)
1. Port clean_orb.py logic to Pine Script v6
2. Validate on TradingView against reconstructed trades
3. Finalize indicator and strategy skeletons

### Phase 5: Community Documentation (1–2 hours)
1. One-page quick reference
2. Step-by-step execution guide with screenshots
3. FAQ

---

## Files Ready to Use

### Python Utilities (Already Written)
- `trading_os/src/strategies/clean_orb.py` — Canonical baseline implementation
- `trading_os/experiments/run_phase7.py` — Phase 7 test suite
- `trading_os/experiments/re_tag_trades_with_ohlc.py` — Trade re-tagging (blocked by OHLC)
- `trading_os/experiments/test_sl_alternatives.py` — SL variant comparison (blocked by OHLC)
- `trading_os/experiments/produce_research_summary.py` — Metrics grouping (already ran)

### Documentation (Already Written)
- `trading_os/MASTER_DOCUMENT.md` — Source of truth
- `trading_os/docs/V1_SPEC.md` — Canonical spec
- `trading_os/docs/COMPONENT_ANALYSIS.md` — Evidence assessment
- `trading_os/docs/COMPONENT_INVENTORY.md` — Component catalog
- `trading_os/docs/PRIORITIZED_COMPONENTS.md` — Priority ranking

### Data (Already Available)
- `strat/data/reconstructed_trades_tagged.csv` — 38 paper trades
- `strat/frd_sample_futures_ES/ES_*_sample.csv` — Sample OHLC (June 2026, doesn't align with trades)

---

## Immediate Action Items (Until OHLC Arrives)

**If waiting for OHLC** (recommended while we await):

1. **Review V1.0 Spec** ([trading_os/docs/V1_SPEC.md](../docs/V1_SPEC.md))
   - Does this match your intended strategy?
   - Any rules missing or contradicting your plan?

2. **Check Component Analysis** ([trading_os/docs/COMPONENT_ANALYSIS.md](../docs/COMPONENT_ANALYSIS.md))
   - Verify priority rankings make sense
   - Agree on testing approach

3. **Prepare OHLC** 
   - Start collecting/exporting ES 1min OHLC for 2026-03-19 to 2026-04-21
   - Test file format (ensure it matches expected schema)

4. **Prepare PINE translation**
   - Review clean_orb.py logic
   - Plan Pine v6 syntax (study Pine docs if needed)

---

## Success Criteria for V1.0

✓ Technical spec written  
✓ Components documented and prioritized  
~ OHLC validation complete (PENDING)  
~ Stop-loss alternatives tested (PENDING)  
~ Retest vs. breakout contradiction resolved (PENDING)  
~ Pine Script translation complete (PENDING)  

**Current progress**: **50% complete** (docs done, validation awaited)

---

## Questions?

Refer to:
- **"What's the strategy?"** → [V1_SPEC.md](../docs/V1_SPEC.md)
- **"What are the issues?"** → [COMPONENT_ANALYSIS.md](../docs/COMPONENT_ANALYSIS.md)
- **"What's the evidence?"** → [MASTER_DOCUMENT.md](../MASTER_DOCUMENT.md) (Evidence section)
- **"What do we do next?"** → See "Next Steps" section above
- **"How to run tests?"** → Each script has `--help` or inline docstring

---

**Status**: Ready for OHLC validation. No further development until OHLC arrives.
