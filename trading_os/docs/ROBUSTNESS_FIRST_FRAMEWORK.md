# Robustness-First Evaluation Framework

**Objective**: Prioritize system **reliability** and **stability** over maximum profit.

---

## The Problem with Profit-First Thinking

Most traders optimize for one metric: **Net Profit**. This leads to:

- ❌ Over-fit systems (optimized to past data, fail in live trading)
- ❌ Complex systems (100+ rules; breaks when market changes slightly)
- ❌ Whipsaw-prone systems (high trade frequency; psychologically exhausting)
- ❌ High-risk portfolios (large drawdowns between wins)
- ❌ Fragile systems (small market regime change causes collapse)

**Example**: A system with +$10,000 P&L but 50% max drawdown is worse than +$5,000 P&L with 15% max drawdown.

---

## Robustness Metrics (In Priority Order)

### 1. **Profit Factor (PF)** — Baseline
- **Definition**: Gross wins ÷ Gross losses
- **Acceptable**: PF > 1.5
- **Good**: PF > 2.0
- **Why**: PF = 1.5 means you make $1.50 for every $1.00 lost; sustainable long-term
- **Caveat**: Can be inflated by lucky month; needs stable PF across months

### 2. **Maximum Drawdown (%)** — Risk Control
- **Definition**: Worst peak-to-trough loss
- **Acceptable**: < 20%
- **Good**: < 10%
- **Why**: If you lose 50%, you need 100% gain to recover. Drawdown compounds risk.
- **Recovery metric**: How many trades to recover from max DD? (ideally < 20 trades)

### 3. **Expectancy ($/trade)** — Consistency
- **Definition**: Average profit per trade (mean P&L)
- **Calculation**: Total P&L ÷ Number of Trades
- **Acceptable**: > 1.0 (positive per trade)
- **Why**: Shows what each trade contributes on average; high variance = unreliable

### 4. **Stability (Month-to-Month Variance)** — Predictability
- **Definition**: Do you make similar money each month, or wildly different amounts?
- **Metric**: Coefficient of Variation (std dev ÷ mean of monthly returns)
- **Acceptable**: CV < 1.0 (returns vary ±30–40% around mean)
- **Red flag**: CV > 2.0 (returns highly unpredictable; regime-dependent)
- **Why**: Consistent $3k/month is better than $0k and $30k months alternating

### 5. **Win Rate** — Psychological Impact
- **Definition**: % of trades that are profitable
- **Note**: NOT the primary goal, but important for psychology
- **Good win rate**: 30–50% is normal for momentum systems
- **Bad sign**: < 20% (too many losers; psychologically hard)
- **Why**: Traders with 70% win rate often quit at small loss streaks

### 6. **Trade Frequency** — Data Quality & Execution Risk
- **Definition**: Trades per week / per day
- **High frequency**: > 5 trades/week (more data, higher execution risk, more costs)
- **Low frequency**: < 0.5 trades/week (less data, easier to execute, but small sample)
- **Ideal**: 1–3 trades/week (balances data quality with reasonable execution)
- **Red flag**: If > 10 trades/day (likely over-fit, whipsaw-prone)

### 7. **Simplicity (Rule Count)** — Robustness to Market Change
- **Definition**: How many rules/filters does the system have?
- **Simpler is more robust**:
  - 1–3 rules: Highly robust (likely to work in different markets)
  - 4–6 rules: Balanced (may need tweaking in different regime)
  - 7–10 rules: Complex (fragile; breaks with market changes)
  - \> 10 rules: Very fragile (optimized to history, not future)

### 8. **Confidence Score** — Statistical Rigor
- **Definition**: How much can we trust these results? (0–100)
- **Components**:
  - Sample size: Need 100+ trades for preliminary, 200+ for robust
  - Date range: Need 6+ months for seasonal effects
  - Trade frequency: Need regular trades, not clustered in one month
- **High confidence (80+)**: Results likely to repeat
- **Medium confidence (50–79)**: Needs validation or larger sample
- **Low confidence (< 50)**: Preliminary only; high variance expected

---

## Robustness Score (Overall)

**Weighted formula** (0–100):
- Profit Factor: 20%
- Drawdown: 25% (recovery ability)
- Stability: 20% (month-to-month variance)
- Confidence: 20% (statistical rigor)
- Simplicity: 10% (robustness to change)
- Win Rate: 5% (psychological tolerance)

**Interpretation**:
- 75–100: **HIGHLY ROBUST** — Ready for production
- 60–74: **ROBUST** — Good for forward testing (paper trade 4 weeks)
- 45–59: **ACCEPTABLE** — Needs refinement before live trading
- 30–44: **WEAK** — High risk; not recommended
- < 30: **UNRELIABLE** — Do not trade

---

## Application to ES/MES ORB Strategy

### Current System (38 trades)

| Metric | Value | Robustness Impact |
|--------|-------|-------------------|
| Profit Factor | 1.78 | ✓ Acceptable (> 1.5) |
| Max Drawdown | ~20%–30% (est.) | ⚠️ High (needs OHLC validation) |
| Expectancy | $62.66/trade | ⚠️ Low confidence (small sample) |
| Monthly variance | Unknown | ⚠️ Need 6+ months data |
| Win Rate | 31.6% | ✓ Acceptable (> 25%) |
| Trade frequency | 2–3/week | ✓ Good (regular, testable) |
| Rule count | 5–7 | ⚠️ Medium complexity |
| Confidence score | LOW (38 trades, uncertain dates) | ⚠️ Needs larger sample |

**Overall robustness score**: ~50/100 (ACCEPTABLE, needs refinement)

**Why?**
- Positive PF and expectancy (good signs)
- But stop-loss results contradict common sense (HYPOTHESIS)
- Retest underperforms breakout (HYPOTHESIS, but N=5)
- Sample too small (38 trades) for robust conclusions
- Uncertainty about exit classification adds risk
- Need larger sample (200+ trades) and OHLC validation to upgrade to ROBUST

---

## Decision Framework: Which System Version to Trade?

**Given System A vs. System B**, choose based on robustness:

1. **Which has higher PF?** (need PF > 1.5 at minimum)
   - If A >> B: Consider A, but check other metrics
   - If similar: Move to next metric

2. **Which has lower max drawdown?** (prefer < 15%)
   - If A >> B: Strong signal for A
   - If similar: Move to next metric

3. **Which has more stable monthly returns?** (prefer CV < 1.0)
   - If A >> B: Strong signal for A
   - If similar: Move to next metric

4. **Which is simpler?** (fewer rules = more robust)
   - If A is 3 rules, B is 8 rules: Choose A (even if B has slightly higher PF)
   - Why: A is more likely to work in different markets

5. **Which has larger sample size?** (prefer 200+ trades)
   - If A has 200+ over 12 months, B has 30 over 2 months: Choose A
   - Why: B's high metrics could be luck; A's are more stable

---

## Red Flags (System Probably Won't Work)

- ❌ PF < 1.3 (margin too small; bad luck kills profits)
- ❌ Max DD > 40% (recovery time too long; portfolio damage too high)
- ❌ Win rate < 20% OR > 80% (either under-traded or heavily optimized)
- ❌ CV > 2.0 (monthly returns unpredictable; regime-dependent)
- ❌ > 15 rules/filters (over-fit; too fragile)
- ❌ Sample < 50 trades (too small; could be luck)
- ❌ All trades in one month (seasonal bias; not tested across conditions)
- ❌ Average trade duration < 2 hours (likely whipsaw; execution risk)

---

## Next Steps: Validation Protocol

Once you build/optimize a system:

1. **In-sample backtest** (current period, 200+ trades):
   - Measure PF, DD, expectancy, stability, simplicity
   - Compute robustness score
   - If score < 60, go back and simplify

2. **Out-of-sample validation** (different time period, 50+ trades):
   - Does the system still work on data it wasn't optimized on?
   - If PF drops > 20%, system is probably over-fit

3. **Paper trading** (live execution, 50+ trades):
   - Track real trade entries/exits vs. backtest assumptions
   - Measure actual fills, slippage, commissions
   - If PF drops > 15%, assumptions were too optimistic

4. **Small live trading** (1 micro contract, 10+ trades):
   - Trade for real, but at minimal risk
   - Confirm psychological tolerance
   - Measure actual P&L vs. expectations

5. **Scale up** (if all passes):
   - Increase to 1 ES or 2 MES contracts
   - Continue monitoring month-to-month variance
   - Adjust if market regime changes significantly

---

## Reference: Robustness Score Calculation

```python
# Simplified version
def robustness_score(pf, dd_pct, cv, sample_size, rule_count, win_rate):
    pf_score = min(100, (pf / 2.0) * 100)  # 100 at PF=2.0
    dd_score = max(0, 100 - (dd_pct * 2))  # 100 at 0%, 0 at 50%
    stability_score = max(0, 100 - (cv * 50))  # 100 at CV=0, 0 at CV=2.0
    conf_score = min(100, (sample_size / 200) * 100)  # 100 at 200 trades
    simp_score = max(0, 100 - (rule_count * 11))  # 100 at 1 rule, 0 at 10 rules
    wr_score = min(100, max(0, (win_rate - 0.25) / 0.25 * 100))  # 100 at 50%
    
    overall = (
        pf_score * 0.20 +
        dd_score * 0.25 +
        stability_score * 0.20 +
        conf_score * 0.20 +
        simp_score * 0.10 +
        wr_score * 0.05
    )
    
    return overall
```

---

**Key Takeaway**: A system with PF=1.8, DD=10%, 30% win rate, and 50 trades is more robust than a system with PF=2.5, DD=40%, 50% win rate, and 40 trades. **Robust > Profitable.**
