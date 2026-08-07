# MASTER TRADING SYSTEM — Source of Truth

Purpose
- The single canonical document that defines concepts, rules, edge cases, version history, and links to research artifacts.

Sections (fill these out first)
- Vision: the project mission and constraints
- Definitions: trading hours, instruments, risk terms, note formats
- Rules: entry rules, exit rules, sizing, risk management
- Filters: market conditions and required filters to enable trading
- Data: canonical data sources and preprocessing steps
- Experiments: pointer to `docs/` research entries
- Change Log: link to `CHANGELOG.md`

Change process
- Every change to rules must be accompanied by a research entry in `docs/` and an entry in `CHANGELOG.md`.

Version: 1.0

---

## Vision

Build a simple, rule-based, data-backed trading system for ES/MES futures that can be:
- Executed consistently by a human trader.
- Backtested objectively.
- Expressed in TradingView indicator and strategy code.
- Explained to other traders and a community.
- Improved over time through documented research.

The system should eliminate emotional decision-making and remove false complexity. Every rule must have evidence or clear logic.

---

## Canonical Rules — V1.0

**Market & Session**
- Symbols: ES (50x multiplier) or MES (5x multiplier)
- Trading hours: 08:00–11:00 ET (forced flat at 11:00 ET)
- Session: Daily; one trade per calendar day maximum

**Opening Range Build**
- Window: 08:00–08:15 ET
- ORB_HIGH = highest price in window
- ORB_LOW = lowest price in window
- ORB_MID = (ORB_HIGH + ORB_LOW) / 2
- Freeze at 08:15 ET; do not update

**Entry**
- Trigger: Close beyond ORB edge (> ORB_HIGH for long, < ORB_LOW for short)
- Confirmation: None (baseline); optional VWAP alignment
- No-trade conditions: ORB range < 5 pts or > 50 pts
- Entry window: 08:15–11:00 ET
- Quantity: 1 contract (ES or MES)

**Exit**
- Stop-Loss: ORB_LOW (long) or ORB_HIGH (short); alternative: ORB_MID
- Take-Profit: 1R (50%), 2R (30%), 3R (20%)  OR  simple single 2R target
- Staircase stop: Move stop to breakeven at TP1, to TP1 at TP2, to TP2 at TP3
- Force flat: 11:00 ET (or market close)

**Filters** (optional)
- VWAP alignment: enabled by default (long above VWAP, short below)
- EMA(50) trend: disabled by default

---

## Current Evidence (Reconstructed Trades, N=38)

**⚠️ IMPORTANT: All findings below are marked with confidence levels. Do not treat hypotheses as validated facts.**

| Metric | Value | Confidence | Implication |
|--------|-------|-----------|-------------|
| Net P&L | $2,381.25 | **LOW** | Small sample (38 trades); positive but high variance expected |
| Profit Factor | 1.78 | **LOW** | PF > 1.0 suggests edge exists, but N too small for certainty |
| Win Rate | 31.6% | **LOW** | 12 wins, 26 losses (high variance with small N) |
| Expectancy | $62.66 / trade | **LOW** | Large expected variance; needs 200+ trades for confidence |
| **Breakout entries (N=33)** | PF=2.03, net=$2,717 | **HYPOTHESIS** | Outperforms retest in sample, but may be labeling bias |
| **Retest entries (N=5)** | PF=0.15, net=-$336 | **HYPOTHESIS** | Underperforms, but N too small; contradicts documentation |
| **Limit/Market exits (N=15)** | PF~14, net=$4,545 | **HYPOTHESIS** | Profitable, but small sample; needs validation |
| **Stop-loss exits (N=22)** | PF=0.07, net=-$2,639 | **HYPOTHESIS** | Underperforming, but unclear if issue is SL placement, entry type, or just sample variance |

**What we know (HIGH confidence):**
- System shows positive returns in 38-trade sample
- Exits vary widely in profitability (Limit/Market >> Stop-loss)

**What we're hypothesizing (LOW confidence, needs validation):**
- Breakout entries outperform retest entries
- Stop-loss placement is suboptimal
- Profit factor will stabilize at ~1.78 with larger sample

**What could change with more data:**
- Finding could reverse (retest actually better)
- Stop-loss could be a labeling issue, not a methodology issue
- Expectancy could be higher or lower
- System could be whipsaw-prone in different market regimes

**Bottom line:** 38 trades show a profitable edge, but findings need OHLC validation and 200+ trade sample before being considered robust.

---

## Research Status

### High Priority (Contradictions / Red Flags)
1. **Retest vs. Breakout**: Documentation claims midpoint retest is the edge; data shows breakout outperforms retest significantly. **Action**: Re-tag trades using OHLC and validate true entry types.
2. **Stop-Loss Performance**: Stop exits have negative expectancy (-$119.94/trade). Limit and Market exits are profitable. **Action**: Test alternative SL placements (tighter stops, time-based stops, breakeven SL).

### Medium Priority (Validation Pending OHLC)
3. **VWAP filter impact**: Default enabled; needs OHLC to measure contribution.
4. **One-trade-per-day enforcement**: Reconstructed data shows multi-trade days; clarify intended behavior.
5. **ORB window (08:00–08:15 vs. 09:30–09:45)**: Both mentioned in research; need to validate which is optimal.

### Low Priority (Future Research)
6. **EMA filter**: Disabled by default; test in future versions.
7. **Adaptive sizing**: Treat as negative hypothesis; likely overfit.
8. **HTF bias, liquidity, FVGs**: Important but require manual annotations.

---

## Links to Research & Documentation

- **Technical Specification**: [V1_SPEC.md](docs/V1_SPEC.md)
- **Component Inventory**: [COMPONENT_INVENTORY.md](docs/COMPONENT_INVENTORY.md)
- **Prioritized Components**: [PRIORITIZED_COMPONENTS.md](docs/PRIORITIZED_COMPONENTS.md)
- **Initial Research Findings**: [RESEARCH_PHASE7_INITIAL.md](docs/RESEARCH_PHASE7_INITIAL.md)
- **Python Implementation**: [src/strategies/clean_orb.py](src/strategies/clean_orb.py)
- **Phase 7 Test Suite**: [experiments/run_phase7.py](experiments/run_phase7.py)
- **Research Summary**: [experiments/outputs/trade_research_summary.json](experiments/outputs/trade_research_summary.json)

---

## Version History

**V1.0** (2026-06-30)
- Simplified ORB breakout entry (vs. retest requirement).
- Fixed SL at ORB edge, multi-level TP.
- One trade/day enforced.
- VWAP optional.
- Known issue: Stop-loss exits underperforming; recommends investigation.
- **Approval status**: Pending OHLC validation.

**V0.9** (Previous)
- Complex multi-filter: retest requirement, adaptive sizing, pyramiding, second trades.
- Marked as overfit based on research.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.
