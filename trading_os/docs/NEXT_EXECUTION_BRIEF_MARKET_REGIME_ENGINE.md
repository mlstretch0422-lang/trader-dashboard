# Next Execution Brief: Market Regime Engine

Date: 2026-07-08
Audience: Any AI collaborator continuing implementation
Priority: Highest

## Mission
Shift research from pure setup validity to context-aware decisioning.

The decision engine must first answer:
- What kind of day is this?
Then answer:
- Should we trade this setup in this regime?

## Do Not Change
Keep these constraints locked:
- max trades per day = 1
- entry window = 9:30 to 10:30 ET
- strategy daily loss stop = 200
- funded-account risk thresholds currently used
- walk-forward and funded diagnostics pipeline

## Module To Build
Create a Market Regime Engine that labels each session before entry logic.

### Minimum regime features
1. Trend day vs range day score.
2. Gap size bucket (small/medium/large).
3. Overnight range percentile.
4. ATR percentile regime.
5. Opening drive strength (first 15-30 minutes).
6. Previous day structure (trend/range).
7. Optional news-day proxy flag.

## Required Data Outputs
For each day:
- regime_label (primary)
- regime_subscores (optional columns)

For each trade and rejected setup:
- attach regime_label
- attach rejection stage from gate funnel

## Reporting Upgrades Required
Every run must output:
1. Expectancy by regime.
2. Trade count by regime.
3. Win rate and PF by regime.
4. Drawdown behavior by regime.
5. Monthly cadence by regime.
6. Rejection-stage frequency by regime.

## Hypothesis Template For First Regime Batch
Hypothesis:
- Edge is regime-conditional; restricting participation to favorable regimes increases expectancy quality and preserves drawdown profile without reducing sample size below viability.

Acceptance criteria:
- Non-degenerate trade count.
- Improvement in expectancy or PF in selected regimes.
- No material DD deterioration.
- Walk-forward remains at least as stable as baseline branch.

## Implementation Notes
- Implement as branch module, not baseline rewrite.
- Keep binary strict filters available, but add regime-gated participation layer.
- Preserve all existing artifacts and diagnostics.

## Deliverables Checklist
- Regime labeling code integrated into optimizer pipeline.
- New regime-aware output CSV/JSON artifacts.
- Updated master transfer doc section with findings.
- One completed research log using RESEARCH_LOG_TEMPLATE.md.

## Suggested First Pass Scope
- Start with 3 broad regimes: Trend, Range, Expansion.
- Evaluate strict and recovery branches under same regime labels.
- Identify where edge actually exists and where system should stand down.
