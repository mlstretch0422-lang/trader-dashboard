# EDGE ATTRIBUTION REPORT

This report summarizes what the current repository actually supports. It separates implementation, historical configuration results, and isolated component evidence.

## Classification language

- **SUPPORTED BASELINE** — enough project evidence exists to keep the component in the reference model, but it is not isolated proof of causality.
- **TESTING** — implemented or historically exercised, but still needs controlled comparison.
- **UNTESTED** — proposed or documented without an accepted comparison record.
- **NEGATIVE EVIDENCE** — the available tested implementation underperformed, without proving every possible version must fail.
- **RETIRED FROM ACTIVE LOGIC** — excluded from the current operating model; may remain as a research control.

## Corrected key findings

- `midpoint retest` is a **SUPPORTED BASELINE / TESTING**, not a proven isolated edge. The strongest exported V6 run reports 156 trades, 39.1% win rate, profit factor 1.431, and 17.75% max drawdown, but the repository does not contain an apples-to-apples midpoint-versus-boundary-versus-immediate-breakout attribution test.
- `retest` is **TESTING with historical support**. Multiple project sources favor break-and-retest execution over blind breakout entry, and retest configurations have positive historical exports, but the effect of the retest layer has not been isolated from timeframe, instrument, filters, sizing, and management.
- Raw `ORB-only` execution is **RETIRED FROM ACTIVE LOGIC** and should be retained only as a control variant. The project direction repeatedly rejects treating an ORB break as automatic trade authorization.
- The `08:00–08:15` ORB appears in the current Pine files and all four rows of `BACKTEST_COMPARISON.csv`, but `STRATEGY_SOURCE_OF_TRUTH.md` names a 09:30–09:45 primary ORB. The clock itself is therefore **TESTING / CONFLICTED**, not settled.
- Session context and higher-timeframe structure are **UNTESTED AS REQUIRED FILTERS** unless a specific accepted output proves their contribution.
- `VWAP` is **TESTING**. It is implemented and repeatedly discussed, but no accepted isolated attribution result is present.
- `EMA`, `ATR regime filtering`, `displacement thresholds`, `volume`, `FVG`, previous-day levels, and news filters remain **UNTESTED or TESTING** according to whether code exists.
- The adaptive second-trade implementation has **NEGATIVE EVIDENCE** in the available MES export: 82 trades, -$203.75 net, profit factor 0.949, and expectancy -$2.48. This rejects that tested variant, not every theoretical second-trade design.

## Historical configuration evidence

| Configuration | Instrument / TF | Date range | Trades | Win rate | PF | Max DD | Expectancy | Classification |
|---|---|---|---:|---:|---:|---:|---:|---|
| V6 ORB Midpoint Continuation | ES / 15m | 2025-04-01 to 2026-02-26 | 156 | 39.1% | 1.431 | $8,875 / 17.75% | $209.94 | Supported research baseline; not isolated |
| V6 ORB Midpoint Continuation duplicate export | ES / 15m | 2025-04-01 to 2026-02-26 | 156 | 39.1% | 1.428 | $9,075 / 18.15% | $208.97 | Reproduction discrepancy to investigate |
| ML R1.3 ORB Retest + Confluence | MES / 5m | 2025-12-08 to 2026-03-20 | 74 | 40.54% | 1.284 | $368.75 / 0.74% | $7.38 | Promising but small and non-isolated |
| ML R1.2 Adaptive Second Trade | MES / 15m | 2025-05-01 to 2026-03-20 | 82 | 43.9% | 0.949 | $1,481.25 / 2.96% | -$2.48 | Negative evidence for this implementation |

Source: `strat/BACKTEST_COMPARISON.csv`.

## Evidence table

| Component | Correct classification | Evidence summary | Required next test |
|---|---|---|---|
| midpoint retest | SUPPORTED BASELINE / TESTING | Positive historical configuration exists; midpoint is current Pine default | Midpoint vs boundary vs immediate on identical data and costs |
| retest layer | TESTING | Positive retest configurations and repeated project preference | Raw ORB control vs ORB + retest |
| raw ORB entry | RETIRED FROM ACTIVE LOGIC | Rejected by current project direction | Keep only as control benchmark |
| ORB clock | TESTING / CONFLICTED | 08:00–08:15 in Pine/backtests; 09:30–09:45 in source-of-truth doc | Same-model clock comparison |
| VWAP | TESTING | Implemented, no accepted isolated attribution | Baseline vs baseline + VWAP |
| EMA | UNTESTED | Optional toggle only | Baseline vs baseline + EMA |
| displacement | TESTING | 35% ORB body or 0.75× ATR implemented | Threshold sensitivity and off/on attribution |
| ORB range gate | TESTING | 5–50 point defaults implemented | Regime buckets and off/on attribution |
| liquidity sweep / reclaim | TESTING | Preferred mechanical direction in research brief | Formal definition, Pine implementation, controlled test |
| higher-timeframe context | UNTESTED AS REQUIRED RULE | Present in research language, not isolated | Define one objective state and test independently |
| volume | UNTESTED | Broad quality idea without quantified rule | Define source, threshold, and no-volume control |
| FVG | UNTESTED | Candidate confluence only | Precise mechanical definition and isolated test |
| second trade | NEGATIVE EVIDENCE | Current adaptive variant PF < 1 and negative expectancy | Re-test only against identical one-trade control |
| adaptive sizing / pyramiding / scaling | UNTESTED OR NEGATIVE | Complexity appears in older builds; no accepted survival improvement | Fixed-size baseline first |

## Governance conclusions

1. A positive strategy export proves only that a complete configuration produced that historical output.
2. It does not prove every component inside the configuration added edge.
3. `PROVEN` must not be used for midpoint, retest, VWAP, EMA, displacement, session context, or other confluences until isolated attribution and holdout evidence exist.
4. The website may show the four historical runs only with instrument, timeframe, date range, sample size, cost-model caveat, and research decision attached.
5. The active Trade Bible must contain accepted operating constraints only. Research components belong in the Strategy Center / Research Vault with visible status labels.

## Next attribution sequence

1. Freeze one baseline configuration and cost model.
2. Reproduce the baseline exactly.
3. Compare immediate breakout, boundary retest, and midpoint retest.
4. Compare ORB clocks on the same history.
5. Test VWAP, EMA, displacement, and range filters one at a time.
6. Run chronological walk-forward validation.
7. Confirm the surviving model in replay or paper-forward execution.

No component is promoted because it appears in code, is common retail practice, or is described as preferred in a research document.
