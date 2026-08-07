# Claude Execution Prompt: Sweep/Rejection Sprint

Use this prompt with Claude as-is.

---

Proceed with the sweep/rejection variant research branch. This is now the highest priority before the Market Regime Engine. Do not increase optimizer trial counts blindly or loosen risk controls globally. Keep Baseline v1.0 locked and unchanged.

Objective:
Determine which sweep/rejection semantics best preserve trade frequency while maintaining funded-account survivability.

Hard constraints to keep fixed:
- max trades/day = 1
- entry window = 9:30-10:30 ET
- strategy daily loss stop = 200
- funded thresholds and walk-forward diagnostics unchanged

Design:
Run 5-8 carefully designed hypothesis variants only (no random variant explosion).

Minimum variant candidates:
1. Delayed reclaim after sweep
2. ATR/volatility-adjusted sweep tolerance
3. Body reclaim rejection instead of wick ratio
4. Engulfing confirmation branch
5. MSS + reclaim branch
6. Weighted confluence scoring branch (experimental; do not overwrite baseline)

For each variant, automatically report:
- Trade count
- Profit Factor
- Net PnL
- Trailing DD survival and max trailing DD
- Static DD survival and max static DD
- Monthly pass cadence
- Walk-forward consistency
- Gate funnel counts
- Sample size quality
- Confidence rating (High/Medium/Low)

Process requirements:
- Hypothesis-first logging per variant
- Supported/Rejected/Inconclusive verdict per variant
- Baseline comparison for every metric
- No promotion if sample size is insufficient or walk-forward is degenerate

Deliverables:
1. Ranked variant comparison table
2. Promotion/rejection decisions with reasons
3. Confidence-tagged conclusions
4. Clear recommendation on whether to proceed to Market Regime Engine next

Relevant local docs:
- trading_os/docs/BASELINE_V1_0_LOCK.md
- trading_os/docs/TRADING_PHILOSOPHY.md
- trading_os/docs/SWEEP_REJECTION_VARIANT_SPRINT.md
- trading_os/experiments/outputs/SUPER_AI_TRANSFER_MASTER_2026-07-08.md
- trading_os/experiments/outputs/RESEARCH_LOG_TEMPLATE.md

---
