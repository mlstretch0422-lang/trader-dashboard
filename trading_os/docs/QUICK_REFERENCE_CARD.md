# ES/MES ORB Strategy v1.0 — Quick Reference Card

**Print this. Keep at desk during market hours.**

---

## Market Setup

| Item | Value |
|------|-------|
| **Symbols** | ES or MES |
| **Session** | 08:00–11:00 ET |
| **ORB Window** | 08:00–08:15 ET |
| **Trade Count** | **1 per day** (max) |

---

## ORB Calculation (08:00–08:15 ET)

1. **Watch the 1-min chart** from 08:00 ET
2. **At 08:15 ET, record**:
   - `ORB_HIGH` = highest price 08:00–08:15
   - `ORB_LOW` = lowest price 08:00–08:15
   - `ORB_MID` = (HIGH + LOW) / 2
   - `ORB_RANGE` = HIGH − LOW
3. **SKIP trading if**:
   - ORB_RANGE < 5 points (too choppy)
   - ORB_RANGE > 50 points (too volatile)
4. **Freeze ORB** — do not update after 08:15 ET

---

## Entry Signal (08:15–11:00 ET)

### Long Entry
- **Trigger**: Close **above ORB_HIGH**
- **Confirmation**: Price > VWAP (optional, default on)
- **Quantity**: 1 contract

### Short Entry
- **Trigger**: Close **below ORB_LOW**
- **Confirmation**: Price < VWAP (optional, default on)
- **Quantity**: 1 contract

### No Entry
- After 11:00 ET (close entry window)
- If already have open trade today (one-trade-per-day)
- If ORB range outside 5–50 point band

---

## Risk Management

### Stop-Loss (SL)
- **Long trade**: SL at `ORB_LOW`
- **Short trade**: SL at `ORB_HIGH`
- **Alternative** (tighter): SL at `ORB_MID`

### Take-Profit (TP)
Split exits (or use single 2R target):

| Level | Price | Exit Qty | Stop Update |
|-------|-------|----------|-------------|
| TP1 | Entry + 1R | 50% | → Breakeven |
| TP2 | Entry + 2R | 30% | → TP1 |
| TP3 | Entry + 3R | 20% | → TP2 |

Where `R` (Risk) = Entry − SL

---

## Execution Timeline

### 07:50–08:00 ET
- [ ] No open positions from yesterday
- [ ] Check calendar for news/holidays
- [ ] Pull up 1-min chart

### 08:00–08:15 ET
- [ ] Monitor high and low
- [ ] At 08:15 ET: record ORB_HIGH, ORB_LOW, ORB_MID
- [ ] Check: Is ORB range between 5–50 points?
- [ ] Set pending stop + TP orders (before 08:15 ET freeze)

### 08:15–11:00 ET
- [ ] Watch for entry signal (close above/below ORB edge)
- [ ] Check VWAP alignment (if enabled)
- [ ] Execute entry order
- [ ] Monitor trade progress
- [ ] Move stop to breakeven at TP1
- [ ] Move stop at subsequent TP hits

### 11:00 ET
- [ ] If trade open, **close at market** (force flat)
- [ ] Record trade: entry, exit, P&L, reason

---

## Performance Targets

**Based on 38 reconstructed trades**:
- **Net P&L**: $2,381 (38 trades)
- **Win Rate**: 31.6% (12 wins, 26 losses)
- **Profit Factor**: 1.78
- **Expectancy**: $62.66 per trade
- **Avg Win**: $452
- **Avg Loss**: -$117

---

## Common Mistakes to Avoid

❌ **Don't** enter after 11:00 ET (window closed)  
❌ **Don't** enter second trade if already have one today  
❌ **Don't** update ORB after 08:15 ET  
❌ **Don't** trade choppy days (range < 5 pts)  
❌ **Don't** trade extremely volatile days (range > 50 pts)  
❌ **Don't** move stop to SL exit level (defeats risk mgmt)  
❌ **Don't** forget to close at 11:00 ET if trade still open  

---

## Optional Filters

### VWAP (Default: Enabled)
- **Long entries**: only if entry price > VWAP
- **Short entries**: only if entry price < VWAP

### EMA(50) (Default: Disabled)
- Can use for additional confirmation (disabled in V1.0)
- Future enhancement

---

## Trade Journal Entry

After each trade, record:
```
Date: 2026-XX-XX
ORB Range: __ pts
Entry Time: __:__ ET, Price: __, Type: [Long/Short], Qty: 1
Exit Time: __:__ ET, Price: __, Type: [TP1/TP2/TP3/SL/Market]
P&L: $___ (__pts × 50 multiplier)
Notes: [reason for entry, any issues]
```

---

## Validation Checklist

Before going live:
- [ ] Backtest on historical data (OHLC provided)
- [ ] Forward-test on paper trading (2+ weeks)
- [ ] Confirm SL alternative tests (pending)
- [ ] Validate VWAP contribution (pending OHLC)
- [ ] Document 20+ trades before real money

---

## Support

**Questions?**
- See [V1_SPEC.md](../docs/V1_SPEC.md) for full technical details
- See [MASTER_DOCUMENT.md](../MASTER_DOCUMENT.md) for strategy rationale
- See [COMPONENT_ANALYSIS.md](../docs/COMPONENT_ANALYSIS.md) for evidence

**Version**: 1.0 (2026-06-30)  
**Status**: Pending OHLC validation
