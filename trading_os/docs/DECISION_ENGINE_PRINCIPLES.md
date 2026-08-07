# DECISION ENGINE PRINCIPLES

Status: Constitutional document
Change policy: Rare updates only; modify only when a principle is proven wrong by evidence.

## Mission

Build a durable, evidence-backed decision engine that captures trader reasoning and survives funded-account constraints.

## Architecture Truth

Expectation first. Observation second. Execution last.

If expectation is unclear, do not execute.
If observation contradicts expectation, invalidate bias and stand down.

## Core Principles

1. Context before confirmation.
2. Higher timeframe context has priority over lower timeframe triggers.
3. Trade the market response to liquidity interaction, not the touch event itself.
4. Classify auction state before evaluating setup quality.
5. One high-quality trade is preferred over multiple mediocre trades.
6. Survival and drawdown control are prioritized over return maximization.
7. A profitable backtest without robustness is rejected.
8. Every new rule must justify its existence with measurable evidence.
9. If a rule cannot be explained clearly, it is not ready for coding.
10. If a rule cannot be measured, it is not promotable.
11. If a rule is not understood, do not optimize it.
12. Promotion requires out-of-sample and walk-forward credibility, not just in-sample metrics.

## Research Governance

- No blind optimizer sweeps on undefined rules.
- New ideas enter as hypotheses with explicit invalidation criteria.
- Module tests precede combined-system tests.
- Any candidate with inadequate sample quality is labeled Inconclusive or Rejected.
- Any candidate violating funded-risk constraints is Rejected regardless of headline PnL.

## Promotion Gate (Minimum)

A rule or module may be promoted only if all are true:

- Mechanically specified with unambiguous conditions.
- Demonstrates adequate sample quality.
- Preserves risk integrity under funded-account constraints.
- Holds acceptable walk-forward behavior.
- Improves system quality versus baseline in a repeatable way.

## Prohibited Behaviors

- Optimizing parameters to compensate for undefined logic.
- Treating indicator alignment as a substitute for context.
- Promoting tiny-sample results due to inflated PF artifacts.
- Changing evaluation criteria after seeing results.

## Operator Standard

The engine should be understandable by a new reviewer without hidden assumptions.
If discretionary language appears, it must be translated into testable proxies before promotion.
