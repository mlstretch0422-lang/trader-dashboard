# RESEARCH GAPS

The following open questions remain after auditing the available research documents. These are the highest-priority gaps to resolve with targeted testing or additional evidence.

1. VWAP confirmation — mentioned as an optional alignment layer, but not proven as a required edge.
2. EMA trend filter — referenced as a possible confluence factor; needs validation.
3. Raw ORB versus retest execution — the biggest gap; research suggests the raw ORB alone is not the edge.
4. Midpoint versus boundary retest — midpoint is supported, but the precise trigger geometry still needs isolation.
5. Stop loss placement rules — only general discipline guidance exists; exact ORB/structure stop rules are undocumented.
6. Take profit architecture — not explicitly defined in the source set.
7. Displacement requirements — research mentions minimum displacement before retest, but the threshold is unspecified.
8. Non-ORB day rules and session behavior — liquidity sweep / equal highs/lows guidance exists, but not a coded rule.
9. 9:30 session timing — advanced rules cite 9:30 EST, while RP research centers on 8:00–8:15; reconcile the two.
10. ATR regime filter — likely helpful, but it is still a hypothesis rather than a proven edge.
11. Volume confirmation and quality — volume is cited as important, but no concrete rule was extracted.
12. Second trade / adaptive sizing / pyramiding / scaling — current evidence suggests these are likely distractions, but they need a clear disproof path.
13. FVG / fair value gap — absent from the current evidence set; either out of scope or not relevant to this method.
14. 2nd trade execution rules — no explicit support in the extracted research; treat as a likely reject unless tested.

## Immediate research priorities

- isolate and test the ORB entry logic with and without a retest layer
- test midpoint retest as the baseline execution model
- quantify whether VWAP/EMA add independent value beyond the retest signal
- define whether session time rules should be based on 8:00–8:15 ORB structure, 9:30 actual market open, or a combination
- treat all adaptive and second-trade ideas as secondary hypotheses, not core edges
