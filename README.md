# Trader Dashboard / Signal Bridge

Signal Bridge is Mason's trading operating system: website, Pine research, strategy evidence, backtests, documentation, and experiment history in one repository.

## Current status

The repository is under active research and refactoring. Trading logic is not production-approved unless the evidence registry says so.

Start here:

- `index.html` — current dashboard application
- `content-status.html` — strategy evidence registry
- `CONTENT_STATUS_AUDIT.md` — human-readable truth audit
- `data/content-status.json` — machine-readable status and historical evidence
- `strat/PHASE7_TEST_PLAN.md` — controlled testing plan
- `strat/PINE_CODE_AUDIT_v1_1.md` — critical audit of current Pine v1.1
- `pine/research/ES_MES_ORB_Attribution_Strategy_v1_2.pine` — clean research baseline
- `experiments/phase7/experiment_manifest.json` — exact experiment queue

## Evidence language

- `VERIFIED` — accepted project rule or governance requirement
- `TESTING` — implemented or historically exercised, but not settled
- `UNTESTED` — proposed without an accepted comparison record
- `RETIRED` — rejected, deprecated, or excluded from active logic

Implementation and backtesting are separate evidence levels. A complete profitable historical configuration does not prove every component inside it.

## Current research baseline

The new attribution script intentionally uses:

- one trade per day
- 09:30–10:30 new-entry window
- 11:00 force flat
- one stop and one target
- optional filters defaulted off
- selectable breakout, boundary-retest, and midpoint-retest modes

This is a test harness, not a live recommendation.

## Validation

Run:

```bash
python scripts/validate_content_status.py
```

The validator checks evidence records, metric provenance, duplicate IDs, and the Phase 7 experiment manifest.

## Contribution workflow

Read `.github/AI_WORKFLOW.md` before changing strategy logic or website claims.

Do not:

- work directly on `main`
- call an implemented toggle proven
- blend historical, replay, paper, funded, and live results
- overwrite failed experiments
- publish proprietary Pine source without Mason's approval
