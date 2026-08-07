# TRADE INTELLIGENCE WEEKLY

Date: 2026-07-08
Scope: Control profile case-study loop closure (no optimizer changes, no new strategy logic).

## Biggest Discovery This Week
The highest-impact difference is not entry alignment. It is post-entry path quality.

- Evidence:
  - Winners average MFE: 14.56 points
  - Losers average MFE: 1.79 points
  - Near misses average MFE: 10.42 points
- Interpretation:
  - Winners and near misses often share similar pre-entry alignment.
  - Outcome divergence is driven by whether the move extends enough to realize full objective vs flattening to non-winning outcomes.

## Strongest Rejected Hypothesis
Hypothesis rejected: EMA, VWAP, MSS, and response confirmation alone separate winners from near misses.

- Evidence:
  - checklist_response_confirmed: winners 12/12, near misses 16/16
  - checklist_vwap_aligned: winners 12/12, near misses 16/16
  - checklist_ema_aligned: winners 12/12, near misses 16/16
  - mss_confirmed: winners 12/12, near misses 16/16
- Conclusion:
  - These are baseline participation conditions, not differentiators for full target achievement.

## Most Surprising Winner
Trade 17, 2022-04-19 09:42, LONG

- Result: +1100.0 USD
- MFE: 22.5 points
- Checklist score: 6
- Single most likely reason it reached full target:
  - Strong extension after confirmation created enough favorable excursion to complete objective.

## Most Surprising Loser
Trade 36, 2026-02-04 09:48, LONG

- Result: -625.0 USD
- MFE: 1.75 points
- MAE: 13.0 points
- Checklist score: 6
- Single most likely reason it failed:
  - Post-entry continuation failed almost immediately despite high pre-entry alignment.

## Most Educational Near Miss
Trade 39, 2026-05-19 10:05, SHORT

- Result: 0.0 USD
- MFE: 23.25 points
- MAE: 12.5 points
- Checklist score: 4
- Single most likely reason it did not achieve full target:
  - Sizable favorable excursion occurred, but trade did not convert to target completion (management/path decay issue).

## One Hypothesis Promoted
Promoted to next experiment queue:

- Hypothesis:
  - Full-target achievement is primarily determined by continuation quality after confirmation, not by additional entry confirmation stacking.
- Confidence: High
- Evidence:
  - Single experiment measured winner-vs-loser separation for continuation and entry metrics.
  - `mfe_pts` separation probability = 1.000 vs entry-quality separation probability = 0.571.
  - `mfe_mae_ratio` separation probability = 1.000.
  - `first5_follow_through_pts` separation probability = 0.976.
- Recommendation:
  - Treat continuation-quality modeling as the primary next research direction.

## One Hypothesis Rejected
Rejected this week:

- Hypothesis:
  - Requiring stronger entry confirmation stack (EMA + VWAP + MSS + response) will separate winners from near misses.
- Confidence: High
- Evidence:
  - All listed confirmations already present at nearly identical rates in winners and near misses.
- Recommendation:
  - Do not add this as a new hard gate.

## One Experiment This Week (Completed)
Experiment: Continuation Quality Split Test

- Goal:
  - Determine whether post-entry continuation quality explains trade outcome better than entry quality.
- Design:
  - Baseline strategy unchanged.
  - Compared winner-vs-loser separation probabilities across entry and continuation metrics.
  - Artifacts:
    - `trading_os/experiments/outputs/trade_case_study_2026-07-08/continuation_quality_trade_metrics.csv`
    - `trading_os/experiments/outputs/trade_case_study_2026-07-08/continuation_quality_separation_report.csv`
    - `trading_os/experiments/outputs/trade_case_study_2026-07-08/continuation_quality_experiment_decision.json`
- Outcome:
  - Decision: PROMOTE continuation-quality direction.
  - Best continuation metric: `mfe_pts` (separation probability 1.000).
  - Entry quality (`checklist_score`) separation probability: 0.571.
  - Continuation metrics materially outperformed entry quality in this test.

## Actionable Conclusion
Finding:
Post-entry continuation quality explains outcome better than entry quality in the completed single experiment.

Confidence:
High

Evidence:
- `mfe_pts` separation probability (win > loss) = 1.000.
- `mfe_mae_ratio` separation probability (win > loss) = 1.000.
- `first5_follow_through_pts` separation probability = 0.976.
- Entry checklist separation probability = 0.571.

Recommendation:
Keep entry logic frozen and prioritize continuation-quality modeling/verification as the next research direction.
