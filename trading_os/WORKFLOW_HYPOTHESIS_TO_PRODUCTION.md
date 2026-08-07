# Workflow: From Hypothesis to Production

**This is your new process for validating trading systems robustly.**

---

## Phase 1: Hypothesis (What You Have Now)

**Status**: 38 trades, 33 days, robustness score 63.9/100 = HYPOTHESIS

### What to do:
1. **Read the evaluation**:
   ```bash
   cat trading_os/ROBUSTNESS_EVALUATION_REPORT.md
   ```

2. **Understand your system's robustness**:
   - Profit Factor 1.78 ✓ (good)
   - Drawdown 29.6% ⚠️ (acceptable but high)
   - Only 2 months history ⚠️ (too short)
   - Confidence: MEDIUM ⚠️ (need larger sample)

3. **Mark all findings as HYPOTHESIS**:
   - Don't claim "stop-loss is bad" — say "appears bad in 38-trade sample"
   - Don't claim "breakout wins" — say "hypothesis: breakout may outperform; needs validation"

### Expected outcome:
- Understand the system is tradeable for testing
- Recognize the limitations (small sample, high DD)
- Know what to validate next

---

## Phase 2: Paper Trading (Validation)

**Goal**: Confirm the system works with real execution

### What to do:

1. **Paper trade 50–100 trades** (2–4 weeks):
   ```
   - Use the QUICK_REFERENCE_CARD as your checklist
   - Track every trade: entry reason, exit reason, actual fill, slippage
   - Note psychology: how do you feel after losses? Can you follow rules?
   ```

2. **Track metrics**:
   - **Actual PF vs. backtest PF**: Should stay > 1.5
   - **Actual drawdown**: Might be higher than backtest (realistic)
   - **Monthly consistency**: Is September profit similar to August?
   - **Execution**: Are fills/slippage reasonable?

3. **Red flags to watch**:
   - PF drops below 1.3 → System may be flawed
   - You skip trades due to fear → Psychological issue
   - Drawdown exceeds 40% → Risk management problem
   - Stops filled at weird prices → Liquidity issue

### Expected outcome:
- Confidence in system execution
- Real-world metrics vs. backtest metrics
- Decision: Proceed to Phase 3 or revise system?

---

## Phase 3: Backtest Validation (Larger Sample)

**Goal**: Confirm findings hold on larger dataset

### What to do:

1. **Generate 200+ trades on real ES data**:
   ```bash
   cd trading_os
   python3 experiments/run_clean_orb_on_sample.py \
     --ohlc frd_sample_futures_ES/ES_real_1min_synthetic.csv
   ```

2. **Re-evaluate robustness on larger sample**:
   ```bash
   python3 experiments/robustness_evaluator.py \
     --trades experiments/outputs/clean_orb_trades.csv \
     --output experiments/outputs/robustness_large_sample.json
   ```

3. **Compare findings**:
   - **38 trades**: 63.9/100 robustness, PF 1.78
   - **200+ trades**: [your larger sample score] robustness, PF [new value]
   - **Did findings hold?** Or did they reverse?

4. **Upgrade confidence levels**:
   - If 200+ trades show PF > 1.7: Upgrade "HYPOTHESIS" → "MEDIUM confidence"
   - If PF < 1.5: Downgrade to "findings may be sample luck"

### Expected outcome:
- Larger sample confirms or refutes hypothesis
- Confidence levels upgraded to MEDIUM or HIGH
- Robustness score stabilized on larger data

---

## Phase 4: Component Validation (Optional, High ROI)

**Goal**: Identify which components actually matter

### What to do:

1. **Test SL alternatives** (30 min):
   ```bash
   python3 experiments/test_sl_alternatives.py \
     --ohlc frd_sample_futures_ES/ES_real_1min_synthetic.csv \
     --trades strat/data/reconstructed_trades_tagged.csv \
     --output outputs/
   ```
   - Compare 6 SL placements
   - Find the one with highest robustness score
   - Expected finding: "SL_MID beats SL_EDGE by +$50/trade" (or not)

2. **Validate retest vs. breakout** (1 hour):
   - Use OHLC to compute true ORB levels
   - Re-tag each trade as true breakout or true retest
   - Compare PF for each group
   - Confirm "breakout wins" hypothesis or find it's sample bias

3. **Measure filter contributions** (1–2 hours):
   - On/off VWAP filter; measure PF delta
   - On/off EMA filter; measure PF delta
   - Identify which filters matter; remove which don't

### Expected outcome:
- Identify highest-impact components
- Remove low-value complexity
- Increase robustness by removing fragile rules

---

## Phase 5: Production Decision

**Gate: Must pass all previous phases before trading live money**

### Approval Checklist

- [ ] Phase 1: Robustness score ≥ 60/100
- [ ] Phase 1: Drawdown < 40%
- [ ] Phase 1: PF > 1.5
- [ ] Phase 2: Paper traded 50+ trades
- [ ] Phase 2: Actual PF within 10% of backtest PF
- [ ] Phase 2: Psychological tolerance confirmed
- [ ] Phase 3: Larger sample (200+ trades) shows PF > 1.5
- [ ] Phase 3: Confidence upgraded to MEDIUM or HIGH
- [ ] Phase 4 (if done): Component testing confirms key hypotheses
- [ ] Phase 4 (if done): Removed low-value filters; increased simplicity

### If all pass:
✅ **Ready for small live trading** (1 MES, $50 risk max/trade)

### If any fail:
❌ **Return to system design**
- Revise rules
- Re-test on paper
- Back to Phase 3

---

## How to Run Each Tool

### Robustness Evaluator (Anywhere)
```bash
python3 trading_os/experiments/robustness_evaluator.py \
  --trades <your_trades.csv> \
  --output outputs/robustness.json

# View results
cat outputs/robustness.json | python3 -m json.tool
```

### Backtest Generator (Real Data)
```bash
python3 trading_os/experiments/run_clean_orb_on_sample.py \
  --ohlc trading_os/frd_sample_futures_ES/ES_real_1min_synthetic.csv

# Output: trading_os/experiments/outputs/clean_orb_trades.csv
```

### Component Tests (Hypothesis Validation)
```bash
# Test 6 SL variants
python3 trading_os/experiments/test_sl_alternatives.py \
  --ohlc trading_os/frd_sample_futures_ES/ES_real_1min_synthetic.csv \
  --trades strat/data/reconstructed_trades_tagged.csv \
  --output outputs/

# View results
cat outputs/sl_alternatives_results.json | python3 -m json.tool
```

---

## Current Status: Where You Are Now

| Phase | Status | What's Done | What's Next |
|-------|--------|-----------|-----------|
| **1: Hypothesis** | ✅ COMPLETE | System evaluated: 63.9/100 | Ready for Phase 2 |
| **2: Paper Trading** | ⏳ NOT STARTED | Ready to trade | Paper trade 50+ trades |
| **3: Backtest Validation** | ✅ READY | Tools built; data available | Run backtest on 200+ trades |
| **4: Component Testing** | ✅ READY | Tools built; ready to run | Optional; high ROI |
| **5: Production** | ❌ NOT APPROVED | Waiting for Phase 2 & 3 | After validation passes |

---

## Decision Tree: What to Do Next?

```
START
  │
  ├─ Want to understand the system?
  │  → Read ROBUSTNESS_EVALUATION_REPORT.md (20 min)
  │  → Read ROBUSTNESS_FIRST_FRAMEWORK.md (20 min)
  │
  ├─ Ready to paper trade immediately?
  │  → Print QUICK_REFERENCE_CARD.md
  │  → Use V1_SPEC.md as your rulebook
  │  → Paper trade 50+ trades
  │  → Measure actual PF vs. backtest
  │
  ├─ Want to validate on real data first?
  │  → Run backtest: run_clean_orb_on_sample.py
  │  → Evaluate: robustness_evaluator.py
  │  → Compare to 38-trade results
  │
  ├─ Want to optimize components first?
  │  → Test SL variants: test_sl_alternatives.py
  │  → Find best performer
  │  → Update V1_SPEC.md
  │  → Then paper trade
  │
  └─ Want to understand why findings might be wrong?
     → Read COMPONENT_ANALYSIS.md (40 min)
     → See all hypotheses marked clearly
     → Understand what could change with more data
```

---

## Key Metrics Reference

### Your Current System (38 trades, 33 days)

```json
{
  "robustness_score": 63.9,
  "assessment": "ROBUST — Good for paper trading",
  "profitability": {
    "profit_factor": 1.78,
    "total_pnl": 2381.25,
    "expectancy": 62.66
  },
  "drawdown": {
    "max_drawdown_pct": 29.6,
    "recovery_trades": 5
  },
  "confidence": "MEDIUM (need larger sample)"
}
```

### Phase 2 Target (Paper Trading)

```json
{
  "target_profit_factor": "> 1.5 (must hold from backtest)",
  "target_win_rate": "> 25% (psychological tolerance)",
  "target_drawdown": "< 40% (risk limit)",
  "trades_to_execute": 50-100,
  "duration": 2-4 weeks,
  "pass_criteria": "PF within 10% of backtest, psychology OK"
}
```

### Phase 3 Target (Larger Backtest)

```json
{
  "sample_size": "> 200 trades (vs. current 38)",
  "date_range": "> 3 months (vs. current 33 days)",
  "target_robustness_score": "> 65/100 (upgrade from current 63.9)",
  "pass_criteria": "Findings hold; confidence upgraded to MEDIUM or HIGH"
}
```

---

## Support

**Questions?**
- System robustness: [ROBUSTNESS_FIRST_FRAMEWORK.md](trading_os/docs/ROBUSTNESS_FIRST_FRAMEWORK.md)
- Your system evaluation: [ROBUSTNESS_EVALUATION_REPORT.md](trading_os/ROBUSTNESS_EVALUATION_REPORT.md)
- Technical spec: [V1_SPEC.md](trading_os/docs/V1_SPEC.md)
- Component details: [COMPONENT_ANALYSIS.md](trading_os/docs/COMPONENT_ANALYSIS.md)

---

**Remember**: The goal is **robustness**, not maximum profit. A system that consistently makes $1,000/month is better than one that makes $0 and $50,000 alternating months.

Ready to start?
