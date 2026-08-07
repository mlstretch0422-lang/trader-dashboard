# Sweep/Rejection Variant Sprint

Date: 2026-07-08
Priority: Highest (before Market Regime Engine)
Status: Planned

## Goal
Determine which sweep/rejection semantics preserve trade frequency while maintaining funded-account survivability.

This sprint is not profit-maximization.
This sprint is semantics validation under locked constraints.

## Locked Constraints (Do Not Change)
- max trades/day = 1
- entry window = 9:30 to 10:30 ET
- strategy daily loss stop = 200
- funded thresholds and walk-forward diagnostics unchanged
- Baseline v1.0 must remain immutable

Reference baseline lock: trading_os/docs/BASELINE_V1_0_LOCK.md

## Research Design
Run a capped hypothesis set (5-8 variants), not random combinatorial explosion.

### Variant Set (v1)
1. Variant A: Delayed reclaim after sweep
- Hypothesis: allowing entry within a short bar window after sweep improves valid sample size without DD degradation.

2. Variant B: ATR-normalized sweep tolerance
- Hypothesis: volatility-scaled tolerance reduces false negatives on high-volatility sessions.

3. Variant C: Body reclaim rejection (instead of wick ratio)
- Hypothesis: close/body reclaim captures intent better than wick-only rejection and improves signal quality.

4. Variant D: Engulfing confirmation branch
- Hypothesis: engulfing confirmation raises quality enough to offset lower frequency.

5. Variant E: MSS + reclaim branch
- Hypothesis: structure shift + reclaim can replace strict wick rejection while preserving edge quality.

6. Variant F: Weighted confluence score branch (experimental)
- Hypothesis: weighted scoring outperforms binary hard-gating in frequency-survivability balance.

Optional additions if capacity allows:
7. Rejection cluster rule (2-of-N bars)
8. Close-back-inside-range rejection semantics

## Required Metrics Per Variant
- Trade count
- Profit Factor
- Net PnL
- Trailing DD breach + max trailing DD
- Static DD breach + max static DD
- Monthly pass cadence
- Walk-forward consistency
- Gate funnel counts
- Sample size quality flag
- Confidence rating (High/Medium/Low)

## Acceptance/Promotion Rules
A variant can be promoted only if all are true:
- Non-degenerate sample size (trades and months above floor)
- No material DD regression
- Walk-forward non-degenerate behavior
- Stable behavior across adjacent seeds/time slices

## Rejection Rules
Reject variant if any:
- Sparse sample masquerading as high PF
- Fold-level degeneration (mostly NO_TRADES)
- DD profile worsens materially
- Improvement disappears with nearby seed changes

## Execution Protocol
1. Record explicit hypothesis per variant.
2. Run variant under identical locked constraints.
3. Export standard artifact pack:
   - orb_v2_optimizer_summary.json
   - orb_v2_optimizer_top50.csv
   - orb_v2_component_attribution.csv
   - orb_v2_gate_funnel.csv
   - orb_v2_walkforward_folds.csv
4. Produce verdict: Supported / Rejected / Inconclusive.
5. Assign confidence using rubric in SUPER_AI_TRANSFER_MASTER_2026-07-08.md.

## Suggested Batch Naming
- opt_sweep_variant_A_delayed_reclaim_<date>
- opt_sweep_variant_B_atr_tolerance_<date>
- opt_sweep_variant_C_body_reclaim_<date>
- opt_sweep_variant_D_engulfing_<date>
- opt_sweep_variant_E_mss_reclaim_<date>
- opt_sweep_variant_F_weighted_score_<date>

## Deliverable
Single ranked variant report with:
- side-by-side metric table
- promote/reject decisions
- confidence tags
- recommended next branch after sprint completion
