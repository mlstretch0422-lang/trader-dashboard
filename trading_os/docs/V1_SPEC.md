# Trading OS — ES/MES ORB Strategy v1.0 Technical Specification

**Version**: 1.0  
**Date**: 2026-06-30  
**Status**: Interim specification (pending OHLC validation)

---

## Executive Summary

This specification defines the simplest, data-backed version of the opening range breakout (ORB) strategy for ES/MES micro e-mini S&P 500 futures. The goal is clarity, testability, and reproducibility.

**Core philosophy**: Single ORB window per session → breakout trigger → simple entry/exit logic → one trade per day maximum.

---

## 1. Market Context & Symbols

- **Symbols**: `CME_MINI:ES1!` (ES, contract multiplier 50), `CME_MINI:MES1!` (MES, contract multiplier 5)
- **Session**: EST (America/New_York), daily structure
- **Timeframe**: 1-minute bars (minute-level precision for entry/exit)

---

## 2. Opening Range Build (ORB)

**Definition**: The high and low recorded during a specific time window at market open.

**Default window**: 08:00–08:15 ET (pre-market, before official US stock market open at 09:30)

**Rule**:
- At market start each day, begin recording high and low from 08:00 ET.
- Continue recording for 15 minutes (until 08:15 ET).
- At 08:15 ET, freeze the ORB high, low, and midpoint. Do not update.
- Calculate: 
  - `ORB_HIGH` = highest price during [08:00–08:15]
  - `ORB_LOW` = lowest price during [08:00–08:15]
  - `ORB_MID` = (ORB_HIGH + ORB_LOW) / 2

**Implementation** (Python):
```python
def compute_orb(df: pd.DataFrame, orb_start_min: int, orb_end_min: int) -> dict:
    """Compute ORB for a day. Returns {'orb_high', 'orb_low', 'orb_mid', 'orb_range'}"""
    orb_section = df[(df['mins'] >= orb_start_min) & (df['mins'] < orb_end_min)]
    if orb_section.empty:
        return None
    return {
        'orb_high': orb_section['high'].max(),
        'orb_low': orb_section['low'].min(),
        'orb_mid': (orb_section['high'].max() + orb_section['low'].min()) / 2.0,
        'orb_range': orb_section['high'].max() - orb_section['low'].min()
    }
```

---

## 3. Entry Conditions

### 3.1 Breakout Detection

**Definition**: A breakout occurs when price closes beyond the ORB edge (high or low).

**Rule**:
- After 08:15 ET, monitor price action.
- Record the first close above `ORB_HIGH` as a **long breakout**.
- Record the first close below `ORB_LOW` as a **short breakout**.
- Once a breakout is detected, the setup is "active."

### 3.2 Entry Trigger

**Current baseline** (V1.0): Immediate breakout entry.  
**Alternative tested**: Midpoint retest (evidence suggests breakout performs better; see research notes).

**Rule (breakout mode)**:
- After a breakout is detected, enter the trade on the next candle close that confirms the direction.
- Long: Enter on close > ORB_HIGH if breakout_long is true.
- Short: Enter on close < ORB_LOW if breakout_short is true.

**Entry timing**:
- Entries allowed from 08:15 ET until 11:00 ET (cutoff time).
- Do not enter after 11:00 ET.

**Entry limit**: One trade per calendar day maximum (enforced via `tradeTakenToday` flag).

### 3.3 No-Trade Conditions

- Do NOT trade if ORB range < 5 points (avoid choppy days).
- Do NOT trade if ORB range > 50 points (avoid extremely volatile days).
- Do NOT trade after 11:00 ET (closes the entry window).

---

## 4. Exit Logic

### 4.1 Take-Profit (TP) Exits

**Rule**: Use a fixed risk/reward structure with two or three exit levels.

**Default configuration**:
- TP1: Entry + 1.0 × Risk (exit 50% of position)
- TP2: Entry + 2.0 × Risk (exit 30% of position)
- TP3: Entry + 3.0 × Risk (exit 20% of position)

where `Risk = Entry - Stop` for longs, `Risk = Stop - Entry` for shorts.

### 4.2 Stop-Loss (SL) Placement

**Evidence from reconstructed trades**: Stop-loss exits dominate losses (PF=0.07, expectancy=-$119.94 per trade). This suggests the current SL placement or methodology is harmful.

**Recommendation for V1.0**: Use the ORB opposite edge as the stop.

**Rule**:
- Long trade: Stop at `ORB_LOW` (or optionally `ORB_MID` for tighter stops).
- Short trade: Stop at `ORB_HIGH` (or optionally `ORB_MID` for tighter stops).

### 4.3 Staircase Stop (Optional)

**Rule**: Move stop to breakeven or prior TP level once profit target is hit.

- If long and price hits TP1, move stop to Entry (breakeven).
- If long and price hits TP2, move stop to TP1.
- If long and price hits TP3, move stop to TP2.

(Mirror for shorts.)

### 4.4 End-of-Day Flat

- Force close all open positions at 11:00 ET (or market close if earlier).
- Execute at market price.

---

## 5. Filters & Context

### 5.1 VWAP Alignment (Optional, Default: Enabled)

**Rule**: Long entries only above VWAP; short entries only below VWAP.

- Compute intraday VWAP using typical price (high + low + close) / 3.
- Only allow long entries if entry price > VWAP.
- Only allow short entries if entry price < VWAP.

**Evidence**: Documented as beneficial in research; pending validation against OHLC.

### 5.2 EMA Trend Filter (Optional, Default: Disabled)

**Rule**: Optional confirmation; long entries only above EMA(50), shorts only below EMA(50).

**Note**: Not enabled by default; recommend testing in future versions.

---

## 6. Position Management

### 6.1 Quantity

- Fixed quantity: 1 contract per trade (ES or MES).
- Commission: ~$1.20 per contract (ES); apply slippage of 2 points.

### 6.2 One-Trade-Per-Day Rule

- Only one live trade allowed per calendar session.
- If a trade is exited early (SL, TP), do not enter another trade the same day.
- Reset `tradeTakenToday` flag at market open (08:00 ET) each day.

---

## 7. Execution Checklist (For Human Trader)

Before market open:
- [ ] Check calendar for market holidays or news events.
- [ ] Confirm no open positions from previous day.

Between 08:00–08:15 ET:
- [ ] Monitor ORB build on chart; confirm high, low, and midpoint visually.
- [ ] Check if ORB range is between 5–50 points.

Between 08:15–11:00 ET:
- [ ] Watch for breakout (close above ORB_HIGH or below ORB_LOW).
- [ ] Confirm entry signal (VWAP alignment if enabled).
- [ ] Place entry order.
- [ ] Place stops and TP orders (TP1, TP2, TP3 if using splits; or single TP at 2R).

At 11:00 ET:
- [ ] If trade still open, close at market (force flat).
- [ ] Review trade: entry reason, exit reason, P&L, trade duration.

---

## 8. Key Performance Indicators (From Reconstructed Trades)

**⚠️ CONFIDENCE LEVELS:** Findings below are marked by confidence (High/Medium/Low/Hypothesis) based on sample size (38 trades) and data coverage.

| Metric | Value | Confidence | Notes |
|--------|-------|------------|-------|
| **Overall (N=38)** | | |
| Net P&L | $2,381.25 | LOW | Small sample; 6-month period |
| Profit Factor | 1.78 | LOW | PF > 1.0 is positive, but N too small |
| Win Rate | 31.6% | LOW | 12 wins, 26 losses (small sample) |
| Expectancy | $62.66/trade | LOW | Large variance with small N |
| **By Entry Type** | | |
| Breakout (N=33) | PF=2.03, Net=$2,717.50 | **HYPOTHESIS** | Outperforms retest in sample, but may be label bias |
| Retest (N=5) | PF=0.15, Net=-$336.25 | **HYPOTHESIS** | Underperforms, but N=5 too small; heuristic-tagged |
| **By Exit Type** | | |
| Limit/Market (N=15) | PF~14, Net=$4,545 | **HYPOTHESIS** | Profitable exits, but small sample |
| Stop-loss (N=22) | PF=0.07, Net=-$2,639 | **HYPOTHESIS** | Losing exits, but may indicate SL placement issue, not exit method |

**Interpretation:**
- ✓ System is **profitable in sample** (PF 1.78 > 1.0), suggesting edge exists
- ⚠️ **Stop-loss vs. Limit/Market difference** is notable but needs validation:
  - May indicate poor SL placement (too tight?)
  - May indicate poor exit timing (exiting too early?)
  - May indicate entry type bias (are losses concentrated in certain setups?)
  - **Confidence: HYPOTHESIS** — Needs OHLC re-tagging and larger sample (200+ trades)
- ⚠️ **Retest vs. Breakout difference** contradicts documentation but N=5 retest trades is too small to conclude
  - **Confidence: HYPOTHESIS** — Requires true entry-type validation with price action

**Next step:** Obtain OHLC data to re-tag trades and upgrade confidence levels to Medium/High.

---

## 9. Version History & Future Research

### V0.9 (Previous)
- Complex multi-filter setup (VWAP, EMA, ATR, body %), retest requirement.
- Adaptive sizing, pyramiding, second trades (now flagged as overfit/distraction).

### V1.0 (Current)
- Simplified: ORB → breakout → immediate entry → fixed SL/TP/staircase exit.
- One trade per day enforced.
- VWAP optional; EMA disabled by default.
- **Known issues**: Stop-loss exits underperforming; recommend alternative SL placement or exit timing.

### V1.1 (Planned)
- Validate retest vs. breakout with OHLC data covering the same date range as reconstructed trades.
- Test alternative SL placements (breakeven after first TP, wider stops, time-based stops).
- Explore tighter SL (e.g., ORB_MID instead of ORB_LOW/HIGH).
- Re-evaluate VWAP and EMA contribution.

---

## 10. Implementation Status

### Python Implementation
- **File**: `trading_os/src/strategies/clean_orb.py`
- **Functions**: `compute_orb()`, `generate_signals()`, `summary_from_trades()`
- **Status**: Beta; tested on sample ES 1-minute data (generated 197 trades across 11 days).

### Pine Script (TradingView)
- **Indicator skeleton**: `trading_os/pine/ORB_Indicator_v1_skeleton.pine`
- **Strategy skeleton**: `trading_os/pine/ORB_Strategy_v1_skeleton.pine`
- **Status**: To be completed after Python validation.

### Backtesting
- **Tool**: `trading_os/experiments/run_phase7.py` (Phase 7 suite).
- **Status**: Runnable on any OHLC CSV.

---

## 11. Next Steps

1. **Validate with OHLC** (high priority):
   - Supply 1-minute MES/ES OHLC covering March–April 2026 (dates of reconstructed trades).
   - Re-tag trades as true retest vs. true breakout.
   - Run component sweep and confirm SL/TP findings.

2. **Test SL alternatives**:
   - Tighter stop (ORB_MID instead of ORB_LOW/HIGH).
   - Dynamic stop (e.g., 1 ATR, 0.5 × ORB_RANGE).
   - Time-based stops (exit after N minutes).

3. **Finalize Pine Script**:
   - Translate clean_orb.py logic to Pine v6.
   - Validate on TradingView chart against reconstructed trades.

4. **Prepare for Discord/Community**:
   - One-page quick reference.
   - Step-by-step execution guide with screenshots.
   - FAQ addressing common mistakes.

---

**Approval**: Pending OHLC validation and SL/TP testing.
