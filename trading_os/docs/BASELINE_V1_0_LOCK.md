# Baseline v1.0 Lock

Date: 2026-07-08
Status: Locked baseline protocol

## Objective
Protect against accidental drift and overfitting by freezing a golden baseline and forcing all new work into research branches.

## Baseline v1.0 Definition
- Engine file: trading_os/experiments/orb_v2_optimizer.py
- Core constraints to preserve in baseline validation runs:
  - max_trades_per_day = 1
  - entry window = 9:30 to 10:30 ET
  - strategy_daily_loss_stop_usd = 200
  - funded risk settings currently used in strict evaluations

## Baseline Artifacts To Keep Immutable
- trading_os/experiments/outputs/opt_funded_recovery_260_retryD/orb_v2_optimizer_summary.json
- trading_os/experiments/outputs/opt_funded_recovery_260_retryD/orb_v2_optimizer_top50.csv
- trading_os/experiments/outputs/opt_funded_recovery_260_retryD/orb_v2_gate_funnel.csv
- trading_os/experiments/outputs/SUPER_AI_TRANSFER_MASTER_2026-07-08.md

## Branching Rule
All new work must use:
- Baseline v1.0 -> Research Branch A/B/C...
Never mutate baseline artifacts after lock.

## Required Batch Metadata
Every experiment must store:
- Hypothesis
- What changed vs baseline
- What remained locked
- Acceptance criteria
- Supported/Rejected verdict
- Confidence level
- Artifact paths

## Promotion Rule
A candidate can be promoted only if:
- Trade sample is sufficient.
- Out-of-sample and walk-forward behavior is non-degenerate.
- Drawdown profile remains acceptable.
- Improvement is persistent across nearby seeds/period slices.

## Failure Rule
If a branch underperforms or is inconclusive:
- Discard branch changes.
- Return to baseline v1.0.
- Open a fresh hypothesis branch.
