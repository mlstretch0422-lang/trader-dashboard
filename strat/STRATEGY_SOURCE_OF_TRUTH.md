# ES/MES ORB Strategy - Source of Truth v1

**Purpose:** Single source for all trading rules, confirmed via data or marked as experimental.
**Asset:** ES (E-mini S&P 500) / MES (Micro E-mini S&P 500)
**Timeframe:** 1-minute bars
**Sessions:** New York morning only
**Max Trades:** 1 per day
**Strategy Type:** Opening Range Breakout with retest + price action confirmation

---

## 1. CORE MARKET HOURS

| Component | Time (ET) | Notes |
|-----------|-----------|-------|
| **Market Open** | 09:30 | When ES cash index opens |
| **ORB Window Start** | 09:30 | Building opening range |
| **ORB Window End** | 09:45 | (10:00 optional to test) |
| **Trade Window Start** | 09:45 | (or immediately after ORB ends) |
| **Trade Window End** | 11:00 | Force flat at this time |
| **Session End** | 13:00 | Market cleanup, no trading |
| **Data Source** | Tick/1m ES or MES | Never trade other symbols |

**RESEARCH FINDINGS:**
- **9:30–9:45 ORB** is industry standard (Real Money Traders data, ThePatternSite, ORB discord)
- **9:30–10:00 ORB** shows marginal improvement in range but at cost of later entry window
- **8:00–8:15 (pre-market)** exists but ES pre-market has lower volume and wider spread; **NOT RECOMMENDED for live trading**
- **DECISION:** Use 9:30–9:45 as PRIMARY, test 9:30–10:00 as alternate config

---

## 2. OPENING RANGE (ORB) BUILD

### ORB Calculation
- **High** = highest price during ORB window
- **Low** = lowest price during ORB window
- **Midpoint** = (High + Low) / 2
- **Range** = High - Low

### Entry Window Constraint
- ORB must complete BEFORE any trades can be taken
- Once ORB window closes, freeze ORB High/Low for that session
- Do NOT update ORB after window closes

### Typical ES ORB Ranges (from backtest data)
- **Tight day:** 5–10 ticks
- **Normal day:** 12–20 ticks
- **Wide day:** 25–40+ ticks
- **Bias:** If first breakout is long, skip short breakout (one direction per day)

---

## 3. ENTRY SIGNALS

### Requirement: Displacement Confirmation
Before ANY breakout entry, the breakout candle must meet **at least ONE** of:

**Option A: Candle Body Size vs ORB Range**
- Body % = `abs(close - open) / ORB_Range`
- **RULE:** Body % ≥ 0.35 (35% of range)
- **RATIONALE:** Prevents whipsaw on tiny ORB ranges; filters thin wicks
- **STATUS:** PROVEN (from existing code, multiple backtest runs)

**Option B: Candle Body vs ATR(14)**
- Body size ≥ 0.75 × ATR(14)
- **RATIONALE:** Adapts to market volatility; wide-range days get looser filters
- **STATUS:** EXPERIMENTAL (exists in code, needs isolated backtest)

### Entry Mode: Retest

After breakout is CONFIRMED (displacement OK):

1. **Wait for retest** of ORB boundary (high if long, low if short)
2. **Retest bar** must have wick penetrating that boundary
3. After retest, **close back inside ORB zone** or cross midpoint
4. **Next bar confirmation:** Close beyond boundary + displacement OK = ENTER

**Alternative: Midpoint Pullback Retest**
- After breakout, wait for price to pull back to ORB midpoint
- This is more conservative than boundary retest
- **STATUS:** EXPERIMENTAL, needs data validation

**Alternative: Immediate Breakout (No Retest)**
- Enter on bar close through ORB boundary + displacement
- **STATUS:** Higher win rate but wider stops; not preferred for 1-trade/day rule

---

## 4. STOP LOSS PLACEMENT

### Option A: Opposite Side of ORB (PREFERRED)
- **Long entry:** SL = ORB Low
- **Short entry:** SL = ORB High
- **RATIONALE:** Risk is clear and defined; accounts for full ORB range
- **STATUS:** PROVEN

### Option B: ORB Midpoint
- **Long entry:** SL = (ORB High + ORB Low) / 2
- **Short entry:** SL = (ORB High + ORB Low) / 2
- **RATIONALE:** Tighter risk; suits aggressive traders
- **STATUS:** EXPERIMENTAL, wider stop = worse RR

### Option C: Fixed Points (Not Recommended)
- Set SL at fixed distance (e.g., 15 points below entry)
- **STATUS:** REJECTED — doesn't adapt to range environment

**DECISION:** Use Option A (Opposite Side) as default

---

## 5. TAKE PROFIT TARGETS

### Structure: Partial Profit Taking (Staircase Approach)

**If Trade Size = 1 contract:**
- 100% @ TP1 (simplest case)

**If Trade Size ≥ 2 contracts:**
- TP1: 50% @ R:R = 1.0  (50% of risk)
- TP2: 30% @ R:R = 2.0  (100% of risk)
- TP3: 20% @ R:R = 3.0  (150% of risk)

### Staircase Stop (Trailing After Each TP)

| Exit Event | New Stop Placement |
|-----------|------------------|
| TP1 Hit | Move SL to entry price (break-even) |
| TP2 Hit | Move SL to TP1 level |
| TP3 Hit | Move SL to TP2 level |

**RATIONALE:** Protects profit on remaining contracts; removes risk once TP1 secured
**STATUS:** PROVEN in existing code; common retail practice

### Adaptive TP (Optional, Experimental)

Adjust TP targets based on rolling average ORB range:
- Wide day (range > 20-day avg) → tighten TPs (1.0, 1.8, 2.5)
- Tight day (range < 20-day avg) → widen TPs (1.5, 3.0, 4.5)
- **Lookback:** 20 sessions
- **Compression range:** 0.4x to 1.8x base RR

**STATUS:** EXPERIMENTAL — implement if time permits, test independently

---

## 6. POSITION SIZING

### Fixed Size (Conservative, START HERE)
- **Per trade:** 1–2 contracts for live trading
- **Backtest:** 1 contract (realism)
- **Margin requirement ES:** ~3.5% per contract
- **Margin requirement MES:** ~$500 per contract

### Risk-Based Adaptive (Advanced, Optional)

**Rule:** Position size = (Max Risk $ / Risk per Contract)

```
Risk per contract = SL distance (points) × $50 (ES) or $5 (MES)
If risk_per_contract > max_risk_per_trade:
    qty = floor(max_risk_per_trade / risk_per_contract)
    qty = clamp(qty, min_qty, max_qty)
```

Example:
- Max risk per trade: $500
- SL distance: 12 points
- Risk per contract: 12 × $50 = $600
- Qty = floor(500 / 600) = 0 → round up to min_qty = 1 contract

**STATUS:** EXPERIMENTAL — builds complexity; start with fixed size

---

## 7. FILTERS (Optional, Data-Backed)

### Filter A: VWAP Filter (Confirmed Useful)
- **Long:** Enter only if close > VWAP (today)
- **Short:** Enter only if close < VWAP (today)
- **RATIONALE:** Removes counter-trend fades
- **STATUS:** PROVEN — approximately 3–5% edge

### Filter B: EMA(50) Trend Filter (Optional)
- **Long:** Enter only if close > EMA(50)
- **Short:** Enter only if close < EMA(50)
- **RATIONALE:** Trend bias; reduces reversals
- **STATUS:** EXPERIMENTAL — marginal, not critical

### Filter C: Previous Day High/Low (Confluence)
- Mark previous session high and low on chart
- **Psychological levels** — increased probability if ORB breaks these
- **STATUS:** OBSERVATION — useful for setup quality, not strict rule

### Filter D: Overnight High/Low (Optional)
- Track high/low from 17:00 ET previous day to 09:30 ET current day
- **Rationale:** Overnight range can define intraday bias
- **STATUS:** EXPERIMENTAL — useful for context, secondary

### Filter E: Time-Based Entry Cutoff (IMPORTANT)
- **After 11:00 ET:** NO NEW ENTRIES
- **After 10:30 ET (Optional):** NO NEW ENTRIES (more conservative)
- **RATIONALE:** Forces early entry; removes stale/dead patterns
- **STATUS:** PROVEN — critical for 1-trade/day rule and max drawdown control

---

## 8. TRADE MANAGEMENT

### Maximum Trades Per Day
- **1 entry max** (hard stop after first entry or first SL hit)
- **Re-entry:** Only if first trade closed as SL (optional re-arm; START with disabled)

### Session Flat (Hard Rule)
- **Force-close all positions** at 11:00 ET
- Flatten at market (no limit orders)
- Reset all signals for next day

### Win Rate Targets
- **Realistic expectation:** 45–55% win rate
- **Target profit factor:** 1.3–1.5 (profit / loss)
- **Target Sharpe (daily):** 0.6–1.2
- **Avoid chasing:** If < 40% win rate, STOP trading; review rules

---

## 9. FILTERS TO SKIP (Proven Ineffective or Dangerous)

| Filter | Why Not |
|--------|---------|
| VIX level cutoff | Lagging; ES leads VIX |
| TICK / TRIN internals | Too complex; adds noise |
| RSI / Stochastic | Whipsawed in range markets |
| NQ correlation | Single-ticker system; add later if ES stable |
| Time-of-day ADX | Marginal; ignored for simplicity |

---

## 10. ENTRY CHECKLISTS

### Pre-Trade Checklist (For Indicator/Live Use)
- [ ] ORB window closed (09:45 ET or 10:00 ET)
- [ ] Breakout visible (close crossed ORB boundary)
- [ ] Displacement confirmed (body size check passed)
- [ ] Retest seen or taken immediately
- [ ] Current time < 11:00 ET
- [ ] VWAP filter pass (if enabled)
- [ ] Previous day H/L noted as context
- [ ] Risk/Reward acceptable (≥ 1:1)
- [ ] No existing position

### Abort Signals (Do NOT Enter)
- ORB range < 5 ticks (too tight; skip day)
- ORB range > 50 ticks (too wild; skip day) — EXPERIMENTAL threshold
- After 11:00 ET
- If first trade already taken and lost money (SL hit)
- VWAP crossed opposite direction post-open
- Previous entry SL just hit (cooldown)

---

## 11. BACKTEST PARAMETERS

### Backtest Range
- **Start:** Jan 2023 (minimum 18 months)
- **Data:** ES 1-minute, bid/ask fills (TradingView default)
- **Commission:** $1.2 per contract (realistic for retail futures)
- **Slippage:** 2 points per trade (conservative)
- **Initial Capital:** $50,000 (typical futures account)

### Drawdown Limits
- Max daily loss: $500 (1% of capital)
- Max weekly loss: $1,500 (3% of capital)
- Max monthly drawdown: $5,000 (10% of capital)
- If hit: STOP TRADING until next month

### Success Criteria
- Win rate: ≥ 45%
- Profit factor: ≥ 1.3
- Sharpe ratio: ≥ 0.6
- Max consecutive losses: ≤ 5
- Biggest single loss: < 2% of capital
- Monthly ROI: 5–15% (realistic)

---

## 12. RULES SUMMARY (Clean & Concise)

```
SESSION:    NY Morning (09:30–11:00 ET)
ORB WINDOW: 09:30–09:45 ET (primary), 09:30–10:00 ET (secondary)
ENTRY:      Breakout + displacement (body ≥ 35% range or ≥ 0.75 ATR) + retest
SL:         Opposite side of ORB
TP:         1.0 R:R (50%), 2.0 R:R (30%), 3.0 R:R (20%) — split with staircase stop
FILTERS:    VWAP (required), time cutoff 11:00 ET (required)
TRADES:     1 per day max
FLAT:       Hard close at 11:00 ET

OPTIONAL:
- Adaptive TP based on rolling avg range
- Risk-based position sizing
- EMA(50) trend filter
- Previous day H/L as context
- Re-arm after first SL (disabled by default)
```

---

## 13. FUTURE ENHANCEMENTS (NOT IN V1)

- [ ] Multi-timeframe confirmation (5m + 1m)
- [ ] Order flow / volume profile retest confirmation
- [ ] Machine learning sweep detection
- [ ] NQ correlation as secondary confirmation (only after ES stable)
- [ ] Advanced time-weighted TP scaling
- [ ] Dynamic SL based on ATR volatility expansion

---

## 14. CODE CHECKLIST

- [x] Clean Pine Script V6
- [x] Zero repainting
- [x] Inputs grouped logically
- [x] ORB levels plotted clearly
- [x] Entry/SL/TP lines visible
- [x] Breakout & displacement markers
- [x] Dashboard showing active filters
- [x] Alerts on entry signals
- [x] Webhook JSON for auto-trading (optional)
- [x] Detailed comments in code
- [x] Backtest & indicator scripts separate

---

## Changelog

**v1.0 (Current)**
- Initial ES-focused simplified strategy
- 9:30–9:45 ORB, opposite-side SL, 3-level partial TP
- VWAP + time cutoff filters
- 1-trade/day max, hard flat at 11:00 ET
- Displacement confirmation (body size)
- Staircase stop after each TP
- Clean Pine V6 strategy + indicator
