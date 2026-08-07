# AI Workflow

This repository is the single source of truth for Signal Bridge.

## Roles

- VS Code/Copilot: primary implementation, local testing, commits, and pushes.
- ChatGPT: repository audit, architecture, strategy-governance review, PR review, and test-plan design.
- Perplexity: external research with citations only.

## Content status labels

Every strategy claim, confluence, indicator rule, metric, or code module must be classified as one of:

- VERIFIED: tested and explicitly accepted in a project source.
- TESTING: currently under defined evaluation.
- UNTESTED: idea or hypothesis with no completed validation.
- RETIRED: rejected, deprecated, or replaced.

Untested material must never be presented as an official strategy rule or premium feature claim.

## Change process

1. Work on a non-main branch.
2. Preserve source evidence and sample-size context.
3. Separate historical backtest, replay, paper, and live results.
4. Open a pull request before merging.
5. Review changed strategy language and code together.
