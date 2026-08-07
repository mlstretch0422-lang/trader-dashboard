# ES ORB Strategy v1.0 - Testing Checklist & Changelog

---

## Testing Checklist (Before Live Trading)

### ✓ Code Validation
- [ ] Strategy compiles without errors (copy into TradingView Pine Editor)
- [ ] Indicator compiles without errors
- [ ] No repainting detected (compare real-time vs closed bar behavior)
- [ ] All inputs accessible and working (try changing each one)
- [ ] Alerts fire on entry signals (test with alert bell sound enabled)

### ✓ Backtest Setup (TradingView)
- [ ] Data source: **ES 1m** (not other symbols)
- [ ] Commission: **$1.20 per round trip** (set in strategy)
- [ ] Slippage: **2 points** (set in strategy)
- [ ] Initial capital: **$50,000** (realistic for futures account)
- [ ] Run from: **January 2023 to present** (minimum 18 months)
- [ ] Timeframe: **1 minute** bars

### ✓ Backtest Results Inspection
After running backtest, verify these metrics:

| Metric | Target | Your Result | Status |
|--------|--------|-------------|--------|
| Total Trades | 50–150 | ___ | ___ |
| Win Rate % | ≥ 45% | ___ | ___ |
| Profit Factor | ≥ 1.3 | ___ | ___ |
| Sharpe Ratio | ≥ 0.6 | ___ | ___ |
| Max Drawdown % | ≤ 15% | ___ | ___ |
| Consecutive Losses | ≤ 5 | ___ | ___ |
| Biggest Loss | < 2% capital | ___ | ___ |
| Avg Win / Avg Loss | ≥ 1.0 | ___ | ___ |
| Exposure Time % | 10–30% | ___ | ___ |

### ✓ Signal Quality Check (Manual chart review)
- [ ] **ORB builds consistently** each day (most days have breakout)
- [ ] **Breakouts have real displacement** (not thin wicks being confirmed)
- [ ] **Retests happen as expected** (for retest modes; breakout mode should have immediate entries)
- [ ] **Stops are outside ORB** (for opposite SL mode; validates placement)
- [ ] **TP levels scale appropriately** (scale with entry distance to SL)
- [ ] **No entries after 11:00 ET** (critical rule working)
- [ ] **Only 1 entry per day max** (one direction only for entire session)

### ✓ Filter Behavior (Test individually)
- [ ] **ORB range filter works**: Skip days with range < 5 or > 50 pts ✓
- [ ] **VWAP filter works**: Long only above VWAP, short only below ✓
- [ ] **Time cutoff works**: No entries after 11:00 ET ✓
- [ ] **Displacement confirmed**: Only trades with body ≥ 35% range ✓

### ✓ Realistic Scenario Testing
Run these backtest variations to confirm robustness:

1. **Low volatility regime** (e.g., May 2023–Jul 2023)
   - Expected: Fewer trades, lower ranges, still profitable
   - Result: _____

2. **High volatility regime** (e.g., Mar 2023, Sep 2023)
   - Expected: More trades, wider ranges, may have larger losses
   - Result: _____

3. **Post-FOMC (earnings) days** (filter Thu/Fri if needed)
   - Expected: Volatile ORBs, wide ranges, higher drawdown
   - Result: _____

4. **Summer/holiday weeks** (Jul-Aug, Nov-Dec)
   - Expected: Thin volume, less reliable breakouts
   - Result: _____

### ✓ Indicator Visual Confirmation
- [ ] **ORB high/low lines draw correctly** on chart
- [ ] **VWAP line displays** (if filter enabled)
- [ ] **Breakout markers show** (triangles at breakout bar)
- [ ] **Entry setup labels appear** (LONG/SHORT setup alerts)
- [ ] **SL/TP guide lines appear** post-setup
- [ ] **Dashboard updates in real-time** with current status
- [ ] **All colors are readable** on your chart background

### ✓ Paper Trading (1 Week Minimum)
- [ ] Trade **live on paper** for 1 full week Mon–Fri
- [ ] Document each trade: entry time, SL, TP, result
- [ ] Verify **alerts are timely** (< 1 min after signal)
- [ ] Verify **you can manually execute** the setup if needed
- [ ] Check for **false signals** and record them
- [ ] Verify **hard flat at 11:00 ET** executes properly

---

## Sample Trade Documentation (For Paper Trading)

Print this table and fill in each trade:

| Date | Time (ET) | Direction | Entry Price | SL | TP1 | TP2 | TP3 | Exit Price | Exit Type | P&L | Notes |
|------|-----------|-----------|-------------|-----|-----|-----|-----|-----------|-----------|-----|-------|
| 6/17 | 09:35 | LONG | 5480.50 | 5475.00 | 5485.50 | 5491.00 | 5496.50 | 5485.50 | TP1 | +$250 | Clean retest |
| | | | | | | | | | | | |

---

## Pre-Live Checklist (When Ready to Trade Real Money)

- [ ] Backtest Sharpe ≥ 0.6 for ≥ 2 years
- [ ] Win rate ≥ 45% (at least 100 trades)
- [ ] 1 week paper trading completed with no major issues
- [ ] Risk per trade set to ≤ 1% of account
- [ ] Max daily loss limit set to 2% of account
- [ ] SL/TP management plan documented and practiced
- [ ] Broker connection tested (IB, TD Ameritrade, etc.)
- [ ] Webhook alerts set up (if using auto-execution)
- [ ] Risk/reward ratio verified for each entry (≥ 1:1 minimum)
- [ ] Journal started (track every real trade)

---

## Common Issues & Troubleshooting

### Issue: "No trades in backtest"
- **Causes:** ORB range filter too tight, VWAP filter too restrictive, wrong symbol
- **Fix:** Lower min range to 3 pts, disable VWAP temporarily, ensure ES 1m data

### Issue: "Too many losing trades"
- **Causes:** Entry mode catching early shakeouts, displacement threshold too low, retest timeout too high
- **Fix:** Increase body % to 0.45, switch to retest mode, reduce timeout to 15 bars

### Issue: "Alerts firing multiple times per bar"
- **Causes:** Code logic error or TradingView script behavior
- **Fix:** Check for duplicate signal generation; add `barstate.isconfirmed` to entry conditions

### Issue: "SL/TP lines not drawing"
- **Causes:** Trade not active, lines disabled in settings, max_lines_count exceeded
- **Fix:** Ensure `i_showSlTpLines = true`, check line count in strategy, delete old objects

### Issue: "Strategy not closing at 11:00 ET"
- **Causes:** Time logic error, timezone mismatch
- **Fix:** Verify timezone setting matches your broker's time, check ET conversion

---

## Changelog

### v1.0 - Initial Release (June 2026)

**Features:**
- ES/MES focused, single symbol only
- 9:30–9:45 ET ORB window (configurable)
- 9:45–11:00 ET trade window (fixed hard close)
- Breakout + displacement confirmation (body ≥ 35% range OR ≥ 0.75 × ATR)
- Three retest entry modes:
  - **Breakout:** Immediate entry on ORB boundary cross + displacement
  - **Boundary:** Wait for wick back to broken ORB boundary, then re-entry
  - **Midpoint:** Wait for wick back to ORB midpoint, then boundary entry
- Stop loss: Opposite side of ORB (high for shorts, low for longs)
- Take profit: 3-level partial (50% @ 1.0 R:R, 30% @ 2.0 R:R, 20% @ 3.0 R:R)
- Staircase stop: SL → entry after TP1, SL → TP1 after TP2, etc.
- Filters:
  - VWAP filter (long above, short below; optional toggle)
  - ORB range bounds (min 5, max 50 pts; skip wide/tight days)
  - Time cutoff (no entries after 11:00 ET)
  - One-trade-per-day maximum
- Hard session flat at user-defined time (default 17:00 ET)
- Clean V6 Pine Script with zero repainting
- Detailed comments and tooltip documentation
- Separate indicator script for live chart guidance
- Webhook-compatible JSON alert messages
- Dashboard showing filter status, ORB info, breakout direction

**Default Settings (Conservative):**
- ORB window: 09:30–09:45 ET
- Trade window: 09:45–11:00 ET
- Displacement threshold: 35% of range
- SL method: Opposite side of ORB
- Entry mode: Boundary retest
- VWAP filter: Enabled
- TP splits: 50/30/20 with R:R 1.0/2.0/3.0
- Staircase stop: Enabled

**Testing Recommendations:**
- Backtest at least 18 months (Jan 2023–present)
- Target: 45–55% win rate, 1.3+ profit factor, 0.6+ Sharpe
- Paper trade 1 week before live
- Document all trades in journal
- Monitor max consecutive losses (target ≤ 5)

**Known Limitations:**
- Single symbol only (no NQ/diversification)
- Assumes liquid ES market (gaps possible pre/post-market)
- Historical backtesting may not predict future performance
- Repainting risk: none (all signals confirmed on bar close)
- Survivor bias: Only tested on ES; may not generalize to other symbols

**Future Improvements (v2.0+):**
- Adaptive TP based on rolling average ORB range
- Risk-based position sizing (not fixed contracts)
- Multi-timeframe confirmation (5m confluence)
- Optional re-arm logic (multiple trades per session)
- EMA trend filter (optional secondary confirmation)
- Integration with portfolio allocation (% account per trade)

---

## Support & Documentation

- **Strategy Rules:** See `STRATEGY_SOURCE_OF_TRUTH.md`
- **Pine Script Docs:** https://www.tradingview.com/pine-script-docs/
- **Backtest Guide:** https://www.tradingview.com/chart/SYMBOL/
- **Community:** TradingView Pine Script forums, ORB Discord communities

---

## Version History

| Version | Date | Status | Notes |
|---------|------|--------|-------|
| v1.0 | Jun 2026 | Released | Initial ES-focused ORB strategy |
| v1.1 | — | Planned | Adaptive TP + risk-based sizing |
| v2.0 | — | Planned | Multi-session + re-arm logic |

