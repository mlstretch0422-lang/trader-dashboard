# EDGE ATTRIBUTION REPORT

This report summarizes the strongest evidence from the available research documents and the current project guidance.

## Key findings

- `midpoint` is **PROVEN**. The RP dossier directly describes the entry as a break/retest around the opening range midpoint.
- `retest` is **LIKELY HELPFUL**. Multiple sources emphasize break-and-retest execution rather than blind breakout entries.
- Raw `ORB` as a standalone edge is **LIKELY HARMFUL**. The dossier explicitly warns that the raw 8:00–8:15 ORB alone is probably not the edge, and a third-party backtest shows low win rate and PF < 1.
- `8:00 – 8:15` as the ORB clock is supported, but the time window is only the structure anchor, not the final trigger.
- `session` context and higher-timeframe structure are **LIKELY HELPFUL**. Research points to HTF candle closes, session filters, and non-ORB day liquidity context.
- `confluence` is **LIKELY HELPFUL**. A confirmation layer with multiple evidence streams is repeatedly framed as necessary.
- `ATR` regime filtering is **LIKELY HELPFUL**. It appears as a reasonable optional filter rather than a core edge.
- `VWAP` and `EMA` are **UNKNOWN**. They are mentioned as possible confirmation alignment layers, but the current source set does not prove their necessity.
- `TP`, `stop loss`, `displacement`, `volume`, `9:30`, `adaptive`, `pyramiding`, `2nd trade`, `scaling`, `FVG`, and `fair value gap` are all **UNKNOWN** in the available evidence.

## Evidence table

| Component | Classification | Evidence summary |
|---|---|---|
| midpoint | PROVEN | Direct RP dossier references to midpoint retest and entry around midpoint.
| retest | LIKELY HELPFUL | Research repeatedly calls out break-and-retest / retest zone language.
| ORB | LIKELY HARMFUL | Research warns raw ORB alone is insufficient; public backtest suggests PF 0.87.
| 8:00–8:15 | PARTIAL EDGE | Supported as the ORB clock; the edge is likely in post-break structure.
| session | LIKELY HELPFUL | HTF context, session zones, higher-timeframe bias and non-ORB day behavior.
| confluence | LIKELY HELPFUL | Confirmation and confluence are named as separate modules.
| ATR | LIKELY HELPFUL | Optional regime filter in build spec.
| VWAP | UNKNOWN | Mentioned in confirmation layer but not independently proven.
| EMA | UNKNOWN | Mentioned as possible alignment; no direct evidence of edge.
| stop loss | UNKNOWN | General trade hygiene in docs, but no fixed rule is documented.
| take profit | UNKNOWN | Not extracted as a specific proven rule in the current research set.
| 9:30 | UNKNOWN | Advanced rules mention 9:30 EST, but core RP evidence is 8:00–8:15 ORB.
| adaptive / 2nd trade / pyramiding / scaling | UNKNOWN / likely harmful | V1 rebuild guidance explicitly bans adaptive sizing and second trades; backtest history flags the 2nd trade feature.
| volume | UNKNOWN | Volume is referenced as a broad execution quality check, not a quantified edge.
| FVG / fair value gap | UNKNOWN | No direct evidence in the current source set.

## Notes

- The available evidence is drawn from the extracted `.docx` sources in `Trade Stratagey`.
- Missing mentions are treated as evidence absence, not as disproof.
- The ORB structure should remain in the system, but the actual edge appears to be in the retest / confirmation / context layers.
- Next step: use this attribution classification to prioritize isolated component tests rather than tuning the entire system at once.

