# AI Contribution Workflow

GitHub is the single source of truth for this project. ChatGPT, VS Code/Copilot, Codex, and external research tools must work from repository state rather than disconnected copies.

## Branch rules

- Never work directly on `main`.
- Use one branch per focused change.
- Keep strategy research separate from production website changes.
- Do not merge a branch that changes trading logic until its evidence status is updated.

Recommended branch prefixes:

- `research/` — hypotheses, tests, experiment outputs
- `pine/` — indicator or strategy code
- `site/` — website changes
- `docs/` — documentation only
- `fix/` — confirmed defects
- `chore/` — governance, automation, or repository structure

## Evidence rules

Every strategy claim must be classified in `data/content-status.json` as:

- `VERIFIED`
- `TESTING`
- `UNTESTED`
- `RETIRED`

Evidence levels are separate from status:

- `PROJECT_RULE`
- `IMPLEMENTED`
- `BACKTESTED`
- `ISOLATED_ATTRIBUTION`
- `WALK_FORWARD`
- `PAPER_FORWARD`
- `LIVE`

Implementation alone never proves edge.

## Required workflow for strategy changes

1. Read `CONTENT_STATUS_AUDIT.md`.
2. Read `strat/PINE_CODE_AUDIT_v1_1.md` when touching Pine.
3. Identify the exact hypothesis being changed.
4. Update or add an experiment in `experiments/phase7/experiment_manifest.json`.
5. Change one primary component at a time.
6. Preserve the previous script and results.
7. Record symbol, timeframe, dates, costs, sizing, and source commit.
8. Update `data/content-status.json` only after evidence exists.
9. Run `python scripts/validate_content_status.py`.
10. Open a pull request and explain what changed, what did not change, and what remains unproven.

## Pine workflow

Research Pine files live in `pine/research/`.

A Pine script can move toward production only after:

- it compiles in TradingView
- timing and state transitions are reviewed
- a known baseline can be reproduced
- the component is tested against a locked control
- walk-forward results are acceptable
- replay or paper-forward execution matches the code

TradingView compilation proves syntax only. It does not prove performance.

## Result storage

Each completed experiment should use an immutable directory such as:

```text
experiments/phase7/outputs/P7-E01-ENTRY-MODE/2026-08-07_<commit>/
```

Store:

- `configuration.json`
- `strategy_tester_overview.csv`
- `list_of_trades.csv`
- `performance_summary.json`
- `equity_curve.csv`
- `drawdown_curve.csv`
- `monthly_results.csv`
- `decision.md`

Do not overwrite prior outputs.

## Website rules

- Active Trade Bible: accepted project rules only.
- Strategy Center: tested configurations and visible evidence status.
- Research Vault: untested hypotheses and external research.
- Version history: retired and replaced logic.
- Metrics: always show source, dates, sample, instrument, timeframe, test type, costs, and decision.

## Tool roles

### VS Code / Copilot / Codex

- edit local code
- run tests and linters
- compile or assist with Pine changes
- commit and push branches

### ChatGPT

- audit repository state
- review strategy logic and evidence quality
- create or update branches and pull requests when connector permissions allow
- reconcile contradictions
- inspect commits and test outputs

### Perplexity or web research tools

- provide external research with direct sources
- do not promote external claims into project rules without repository review and testing

## Hard prohibitions

- no unsupported “proven” claims
- no blended backtest/paper/live performance
- no silent parameter changes
- no deleting failed experiments
- no optimizing many layers at once
- no publishing proprietary Pine source without Mason's approval
- no merging to `main` only because code compiles
