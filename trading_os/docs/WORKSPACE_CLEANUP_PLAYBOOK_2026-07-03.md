# Workspace Cleanup Playbook

Date: 2026-07-03
Mode: Non-destructive (move/archive/index only)

## Why
The workspace has valuable strategy assets and many outputs, but navigation friction causes missed signals and repeated testing.

## Cleanup Rules
- Do not delete strategy/data/history files.
- Move clutter to clearly named archive folders.
- Keep canonical strategy/optimizer files in-place.
- Add index files at each high-volume folder.

## Priority 1: Outputs Folder Hygiene
Folder: `trading_os/experiments/outputs/`

Steps:
1. Move `trades_combo_*.csv` to `_archive_candidates/trades_combo/`.
2. Keep summary artifacts and named run folders in root outputs.
3. Maintain `_index/OUTPUTS_INDEX.md` as source of truth.

## Priority 2: Strategy Asset Traceability
File: `trading_os/docs/STRATEGY_ASSET_MAP.md`

Steps:
1. For each legacy strategy artifact, extract explicit rules.
2. Map each rule to code status: implemented / partial / missing.
3. Add new optimizer toggles only for explicit extracted rules.

## Priority 3: Legacy Folder Stabilization
Folder: `strat/Trade Stratagey/`

Recommended future move set:
1. Create `strat/archive/2026-07-03_trade_stratagey_snapshot/`.
2. Move raw screenshots, one-off spreadsheets, and duplicate exports there.
3. Keep only active references in `strat/research_texts/` and `strat/data/`.

## Priority 4: Standard Experiment Lifecycle
1. Batch run creates date-stamped artifact files.
2. Record top-3 candidate IDs in a short markdown note.
3. Validate candidates with walk-forward + funded constraints.
4. Promote winning params into a tracked release note.

## Immediate Next Actions
1. Finish hardened forced-short batch and rank eligible candidates.
2. Archive `trades_combo_*.csv` into `_archive_candidates/trades_combo/`.
3. Create one consolidated leaderboard CSV for all optimization runs.
