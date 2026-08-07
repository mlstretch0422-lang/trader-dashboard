# CURRENT STATE OF MASON'S TRADING SYSTEM
## Complete Audit Report - June 16, 2026

---

## 1. EXISTING STRATEGIES & CODE

### V6 Adaptive ORB Strategy
**File:** `pre built orb strat.txt` (2,237 lines)
**Status:** Complex, multi-session, production-ready
**Features:**
- Three sessions: NY (6:30–13:00 ET), Asia (15:00–00:00), London (00:00–06:30)
- Adaptive position sizing (risk-based, not fixed)
- Adaptive take profit scaling (range-based multiplier)
- Per-session rolling average tracking (20-session lookback)
- Advanced re-arm logic (multiple trades per session)
- Staircase stop implementation
- JSON webhook alerts (TradersPost/Ghost compatible)
- Dashboard with status display
- Previous day H/L tracking
- Custom line/label drawing

**Complexity Issues:**
- Multi-session makes it hard to isolate which session drives performance
- Adaptive sizing adds many variables (max risk, min qty, max qty)
- Adaptive TP compression (0.4x–1.8x) is not tested independently
- Three session types create three different risk/reward profiles
- Session-specific day filters (Mon/Fri only for NY, Thu only for Asia, etc.)

### V5 ORB Indicator
**File:** `perp orb.txt` (incomplete, first 500 lines visible)
**Status:** Prototype, midpoint continuation focus
**Features:**
- 8:00–8:15 ORB window (pre-market)
- 9:30–11:00 trade window
- Breakout + displacement confirmation
- Midpoint pullback depth calculation (shallow/deep/valid)
- Reclaim/trigger logic
- VWAP + EMA filters
- Filter dashboard with environment scoring

**Conflict with V6:**
- V5 uses 8:00–8:15 ORB (pre-market, lower volume)
- V6 strategy focuses on 6:30 start (even earlier)
- Different ORB windows = different setups being tested

### v1.0 Simplified ES-Only Strategy (JUST CREATED)
**File:** `ES_ORB_Strategy_v1.0.txt`
**Status:** Clean, baseline reference
**Focus:** Single ES symbol, 9:30–9:45 ORB only
**Simplifications:** Fixed sizing, single session, no re-arm

---

## 2. DOCUMENTED RULES & BELIEFS

### What You Currently Believe (From Strategy Source of Truth)

#### ✅ PROVEN (Labeled in strategy docs)
1. **9:30–9:45 ORB is industry standard** for ES (research cited: Real Money Traders, ThePatternSite, ORB discord)
2. **Breakout + displacement confirmation** reduces whipsaws (body ≥ 35% range OR ≥ 0.75 × ATR(14))
3. **Opposite-side SL** (ORB high/low) is clear and defined
4. **Staircase stop** (SL → entry after TP1) is common practice and protects profit
5. **VWAP filter** improves win rate 3–5% (approximate, not precisely measured)
6. **One trade/day maximum** aligns with single ORB window reality

#### 🟡 EXPERIMENTAL (Labeled, untested in isolation)
1. **9:30–10:00 ORB alternative** (marginal improvement claimed, but at cost of later entry window)
2. **ATR-based displacement (0.75 × ATR)** as alternative confirmation
3. **Midpoint pullback retest** vs boundary retest (which is better?)
4. **Adaptive TP scaling** (0.4x–1.8x multiplier based on rolling range average)
5. **Adaptive position sizing** (risk-based rather than fixed contracts)
6. **Re-arm after SL** (multiple trades per session; adds complexity)
7. **EMA(50) trend filter** as secondary confirmation
8. **Previous day high/low as confluence** level

#### 🔴 REJECTED (Not explicitly labeled, but not in default strategy)
1. **Pre-market 8:00–8:15 ORB** (V5 used it, but V6 moved away; lower volume concern)
2. **NQ correlation** as confirmation (mentioned in brief but not implemented as requirement)
3. **VIX / TICK / ADD internals** (mentioned but rejected as "too complex")
4. **Multi-symbol diversification** (ES-only focused by design)

---

## 3. CONTRADICTIONS & CONFLICTS

### **Conflict 1: ORB Window Selection**

**What the docs say:**
- **Primary:** 9:30–9:45 ET (in v1.0 strategy, source of truth doc)
- **Alternative:** 9:30–10:00 ET (mentioned but not tested)

**What the code shows:**
- **V5 indicator:** 8:00–8:15 ET (pre-market, older approach)
- **V6 strategy:** 6:30 ET start (even earlier, Asia hours)

**Impact:** Different ORB times = completely different market regimes
- Pre-market has wider spreads, lower volume, gap risk
- 9:30 cash open is liquid, tight spreads
- Each should be tested independently

**Current Status:** UNTESTED ISOLATION - which one actually works?

---

### **Conflict 2: Entry Mode Confusion**

**What the docs say:**
- Retest mode preferred (wait for pullback, then re-entry)
- Three options: Breakout (immediate), Boundary (retest edge), Midpoint (retest mid)

**What the code shows:**
- V5 uses complex pullback depth logic (shallow/deep/valid thresholds)
- V6 has re-arm logic after exits (multiple entries per session)
- v1.0 has three selectable modes but unclear which is tested

**Issue:** No clear winner documented. No data showing:
- Win rate: Immediate breakout vs retest
- Win rate: Boundary retest vs midpoint retest
- Sample sizes tested

---

### **Conflict 3: Position Sizing**

**What the docs say:**
- "Start with fixed size (1–2 contracts)"
- Adaptive sizing is optional and experimental

**What the code shows:**
- V6 strategy USES adaptive sizing by default
- Requires calculating risk-per-contract dynamically
- Adds complexity: min qty, max qty, max risk per trade

**Issue:** If adaptive sizing is experimental, why is it in production code? Not clear if results are:
- With fixed 1 contract?
- With adaptive sizing?
- Tested separately?

---

### **Conflict 4: Stop Placement Method**

**What the docs say:**
- **Opposite side (preferred):** SL = ORB high or low
- **Midpoint (experimental):** SL = (ORB high + low) / 2

**What the code shows:**
- V5 has only midpoint-zone logic (± 15% of range around mid)
- V6 has multiple SL methods but defaults unclear

**Issue:** Different stop placements = completely different risk metrics
- Opposite side = larger stops on tight ORBs
- Midpoint = tighter stops on wide ORBs
- Profit factor will vary significantly

---

### **Conflict 5: Filter Weighting**

**What the docs say:**
- VWAP filter is strongly recommended
- EMA(50) filter is optional

**What the code shows:**
- V5 dashboard tracks VWAP + EMA + environment scoring
- V6 has all three enabled by default

**Issue:** No clear evidence of which filter (if any) has highest edge
- Is VWAP + EMA a net positive or does it cut too many trades?
- No win rate comparison with/without filters

---

### **Conflict 6: Session Trading Rules**

**What the docs say:**
- Single NY morning session (9:30–11:00 ET)
- Hard flat at 11:00 ET (critical rule)

**What the code shows:**
- V6 has THREE sessions simultaneously (NY, Asia, London)
- Each session has separate position, SL, TP, re-arm settings
- Can have 3 open positions at once (one per session)

**Impact:** Completely different risk profile
- Single session = low correlation, simple management
- Multi-session = correlated trades possible, complex exit management

---

### **Conflict 7: Trade Journal Data Quality**

**What exists:**
- 2 paper trading journal exports (March 26, April 6, 2026)
- Multiple order history exports from April
- Partial data for several trading days

**What's missing:**
- Pre-market analysis notes (what setups were you looking for?)
- Trade-by-trade commentary (what made you enter/exit?)
- P&L per trade (only order fills visible, not trade results)
- Win/loss categorization
- Setup type categorization (breakout? retest? which pattern?)

---

## 4. DATA AVAILABLE FOR ANALYSIS

### Trading Data
- ✅ **Paper trading journals:** 2 files (March 26, April 6, 2026)
- ✅ **Order history:** 7 files spanning April 6–21, 2026
- ✅ **Trading data timeframe:** Limited (~3 weeks of paper trading)
- ❌ **No live performance data** (backtests only)
- ❌ **Win/loss breakdown not explicitly tracked**
- ❌ **Setup categorization not recorded**

### Backtest Data
- ✅ **4 backtest Excel files** (different strategy versions):
  - ML_R1.2: Adaptive 2nd trade (March 23)
  - ML_R1.3: ORB Retest + Confluence (March 21)
  - V6 ORB Midpoint Continuation (2 copies, March 23)
- ❌ **Date ranges not visible** (need to extract from files)
- ❌ **Backtest parameters not documented** (commission? slippage?)
- ❌ **Backtest results not summarized** (need to extract)

### Research Material
- ✅ **Strategy brief:** Trading_Strategy_V1_Restart_Brief.docx
- ✅ **ORB research:** RP_Profit_8am_ORB_Research_Dossier.docx
- ✅ **Pine Script checklist:** Pine_Script_V6_Writing_Dictionary_and_Anti_Stupid_Checklist.docx
- ✅ **Operating checklist:** AI_Trading_Project_Operating_Checklist.docx
- ✅ **Trade Bible:** Multiple PDFs and docs
- ❌ **Structured research summary** (findings buried in docs)

---

## 5. RULES THAT APPEAR REPEATEDLY

### Across All Versions
1. **ES/MES only** (no NQ, no forex, no crypto)
2. **1-minute bars** (only timeframe tested)
3. **ORB-based entry** (all versions use ORB concept)
4. **Morning session focus** (all versions trade NY morning)
5. **Hard time cutoff** (all versions stop entries by 11:00–13:00 ET)
6. **One trade per day preferred** (mentioned in docs, implemented as rule)
7. **VWAP filter present** (in v5, v6, v1.0)
8. **Displacement/body size confirmation** (in all versions, 35% or 0.75 ATR)

### What's Inconsistent Across Versions
1. **ORB window:** 8:00–8:15 (V5) vs 9:30–9:45 (v1.0) vs 6:30 (V6) vs 9:30–10:00 (mentioned)
2. **Entry mode:** Immediate vs retest vs depth-based
3. **Stop placement:** Opposite side vs midpoint vs midpoint-zone
4. **Session count:** Single (V5, v1.0) vs three (V6)
5. **Re-arm logic:** None (V5, v1.0) vs optional (V6)

---

## 6. WHAT IS OBJECTIVE (Data-Backed)

From backtest Excel files (assuming they ran):
- ✅ Win rate by version (if extracted)
- ✅ Number of trades tested (if dates visible)
- ✅ Profit factor (if calculated)
- ✅ Max drawdown (if tracked)
- ✅ Which session performed best (if V6 data separated)
- ✅ Which ORB time performed best (if tested separately)

From paper trading (partial):
- ✅ Order fills and sizes (visible in journal)
- ❌ Actual P&L (not shown, only order events)
- ❌ Win rate (would need to categorize each trade)
- ❌ Average trade (would need entry/exit prices and dates)

---

## 7. WHAT IS SUBJECTIVE (Opinion-Based)

From docs and code:
- 🟡 **"VWAP filter adds 3–5% edge"** — approximate, not measured precisely
- 🟡 **"Displacement confirmation prevents whipsaws"** — logical but not quantified
- 🟡 **"Retest mode improves quality"** — fewer trades claimed, but win rate not compared
- 🟡 **"One trade/day reduces drawdown"** — intuitive but not tested vs multiple-entry version
- 🟡 **"Staircase stop protects profit"** — common practice but specific impact not measured

---

## 8. ASSUMPTIONS WITHOUT EVIDENCE

1. **8:00–8:15 ORB is viable** — mentioned but dismissed without backtest data
2. **9:30–10:00 ORB is "marginal improvement"** — stated but never tested
3. **Pre-market spread is too wide** — assumed, not quantified
4. **Adaptive TP scaling improves performance** — implemented but not tested in isolation
5. **Re-arm should be optional** — good instinct, but no data on whether it's + or −
6. **50/30/20 TP split is optimal** — standard practice but not tested vs 33/33/33 or 50/50
7. **VWAP filter > EMA filter** — asserted but not compared head-to-head

---

## 9. TESTING GAPS

### Missing Comparative Tests
- [ ] 8:00–8:15 ORB vs 9:30–9:45 vs 9:30–10:00 (isolated)
- [ ] Immediate breakout vs boundary retest vs midpoint retest (head-to-head)
- [ ] Opposite-side SL vs midpoint SL (same dataset)
- [ ] With VWAP filter vs without (win rate %)
- [ ] With EMA filter vs without (win rate %)
- [ ] Single session (NY only) vs multi-session (V6) on same dates
- [ ] Fixed 1 contract vs adaptive sizing (same market)
- [ ] 50/30/20 TP split vs other splits
- [ ] Different displacement thresholds (35% vs 40% vs 50%)

### Missing Data Extraction
- [ ] Backtest results from Excel files (dates, stats, per-trade data)
- [ ] Paper trading P&L per trade (calculated from journal + order data)
- [ ] Win rate by month (seasonality analysis)
- [ ] Win rate by day of week (Mon/Fri better/worse?)
- [ ] Correlation between ORB range size and profitability
- [ ] Average trade duration (entry to exit time)

---

## 10. SUMMARY: CURRENT STATE

### What's Working
✅ Clear ORB logic (defined, consistent, testable)
✅ Multiple entry modes coded (can test separately)
✅ Displacement confirmation logic (reduces noise)
✅ Risk management framework (SL/TP/staircase stop)
✅ Code is modular enough to test components independently
✅ Paper trading has started (real market data exists)

### What Needs Clarification
🟡 Which ORB window is actually best? (3 different times coded)
🟡 Which entry mode performs best? (3 options, no head-to-head test)
🟡 Is adaptive sizing helping or hurting? (assumed good, not tested)
🟡 Do filters help or hurt? (seem important but not quantified)
🟡 What's the real win rate? (mixed across versions, unknown overall)

### What's Missing
❌ Unified dataset with all trades categorized
❌ Apples-to-apples comparison of different versions
❌ Statistical significance testing (sample sizes unclear)
❌ Honest backtest results summary (4 files exist but not extracted)
❌ Journal with pre-market analysis + post-trade review
❌ Definition of what counts as "valid" setup vs "noise"
❌ Rules for which trades to take vs skip

---

## 11. CRITICAL QUESTIONS TO ANSWER

Before you trade real money:

1. **Which ORB window should be primary?**
   - Test 8:00–8:15 vs 9:30–9:45 vs 9:30–10:00 on same backtest date range
   - Measure: Win rate, profit factor, average trade size, drawdown

2. **Does retest entry actually help?**
   - Compare immediate breakout vs boundary retest vs midpoint retest
   - Same market, same dates, control for everything else

3. **What's the real win rate?**
   - Extract actual results from 4 backtest Excel files
   - Combine into single dataset with comparable parameters

4. **How much does VWAP filter matter?**
   - Run same strategy with VWAP on vs off
   - Measure: Win rate increase, trade count decrease, profit factor

5. **Should you use adaptive sizing or fixed?**
   - Run v1.0 (fixed 1 contract) vs V6 (adaptive) on same dates
   - Measure: Which has better Sharpe ratio? Which has fewer drawdown periods?

6. **Is multi-session better than single-session?**
   - Run v1.0 (single NY) vs V6 (3 sessions) on same dates
   - Measure: Monthly ROI, max drawdown, correlation between sessions

---

## 12. NEXT IMMEDIATE STEPS (Phase 2)

1. Extract results from 4 backtest Excel files
2. Extract P&L from paper trading journals
3. Create unified trading dataset with all historical trades
4. Build comparison table: version vs win rate vs profit factor
5. Identify which tests have been run vs which haven't
6. Create MASTER_TRADING_SYSTEM.md with all rules organized
7. Propose specific backtest experiments to run next

---

**Report Generated:** June 16, 2026  
**Status:** Audit complete, ready for Phase 2 (Master Strategy Document)  
**Recommendation:** Before building anything new, extract and analyze the 4 backtest files to understand what has actually been tested vs what is assumed.
