# Trading Philosophy

Date: 2026-07-08
Status: Active guardrail document

## Purpose
This system is not a single strategy script. It is a research and execution operating system designed to discover, validate, deploy, and continuously improve edges under strict risk controls.

## Core Principles
1. Survival first.
- Protect downside before maximizing upside.
- Trailing drawdown survival has priority over cosmetic backtest returns.

2. Process over prediction.
- We do not predict every day.
- We classify market context, then decide whether participation is justified.

3. Mechanical execution over discretionary impulse.
- Entry, risk, and stop logic must be explicitly codified.
- Emotional overrides are treated as process defects.

4. Evidence beats opinion.
- Every change must be tied to hypothesis, test, and artifact.
- No parameter changes without a documented rationale.

5. One trade can be enough.
- Selectivity is a feature, not a flaw.
- If there is no valid edge in current context, no trade is the correct trade.

6. Consistency over excitement.
- Monthly and risk-adjusted stability matter more than occasional outlier wins.

7. System integrity is non-negotiable.
- Do not modify strategy logic to hide data issues.
- Fix data quality first; preserve decision logic intent.

## Why Funded-Account Constraints First
- Capital efficiency and external risk limits enforce discipline.
- Strategy robustness is measured against realistic operational constraints.
- If edge cannot survive funded constraints, it is not production-ready.

## What Counts As Edge
An edge is only accepted if all are true:
- Positive expectancy with adequate sample size.
- Survives out-of-sample and walk-forward evaluation.
- Maintains acceptable drawdown behavior.
- Shows repeatable behavior in identifiable market contexts.

## What Can Change
- Confluence definitions, weights, and context filters.
- Feature engineering and market regime classification.
- Execution details only when validated by evidence.

## What Must Not Change Without Formal Re-Baselining
- Core risk controls (trade/day limits, loss-stop framework, funded constraints).
- Evaluation standards (walk-forward, diagnostics, attribution, confidence rubric).
- Research discipline (hypothesis-first and artifact-backed conclusions).

## Daily Stop Conditions
Stop trading for the day when any condition is hit:
- Strategy daily loss stop reached.
- Behavioral process breach (rule violation).
- Market context invalidates the approved setup universe.

## Invalidation Conditions For The Current System
The system is considered invalid until repaired if one or more occur:
- Edge disappears across sufficiently large out-of-sample windows.
- Drawdown profile breaches risk tolerances persistently.
- Signal quality depends on narrow history slices only.
- Diagnostics show decision engine collapse under realistic constraints.

## Long-Term Vision
Build a reusable research platform:
Market State -> Bias -> Opportunity -> Confirmation -> Risk -> Execution -> Review

This framework should evaluate ORB-derived and non-ORB ideas without rebuilding the entire stack.
