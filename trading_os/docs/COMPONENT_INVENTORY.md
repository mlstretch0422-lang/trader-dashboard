## Component Inventory — ES ORB Retest System

This file lists identified strategy components, their intended purpose, canonical rule (where available), source files, and current testability status.

- **ORB Window (structure)**
  - Purpose: define session structure (high/low/mid) used as reference levels.
  - Canonical: `i_orbStart` / `i_orbEnd` (defaults in `ES_ORB_Strategy_v1_1_FIXED.txt`: 0800–0815). Source: `strat/ES_ORB_Strategy_v1_1_FIXED.txt`.
  - Testable: requires OHLC with matching timestamps. Status: pending OHLC validation; sample data present but does not cover reconstructed trade dates.

- **Retest Mode (entry type)**
  - Purpose: require a break + retest (Midpoint / Boundary / Breakout) before entry.
  - Canonical: `i_retestMode` (default Midpoint). Source: `ES_ORB_Strategy_v1_1_FIXED.txt`.
  - Testable: needs OHLC to validate price interaction with ORB mid/boundary. Partial evidence: reconstructed trades labeled `retest` (heuristic) underperform `break` in current paper-trade dataset (see research summary).

- **VWAP filter**
  - Purpose: alignment filter (long only above VWAP, short only below).
  - Canonical: `i_useVWAP` (default true). Source: `ES_ORB_Strategy_v1_1_FIXED.txt`.
  - Testable: requires OHLC + intraday VWAP calculation. Status: pending OHLC validation.

- **EMA filter**
  - Purpose: trend alignment; `i_useEMA`, `i_emaLen` (default 50).
  - Testable: requires OHLC. Partial tests with synthetic data executed.

- **Body / ATR displacement filters**
  - Purpose: require sufficient breakout body size relative to ORB range or ATR: `i_bodyMinPct`, `i_bodyMinAtr`, `i_atrLen`.
  - Testable: requires OHLC.

- **Range filters (min/max ORB)**
  - Purpose: skip days with ORB range < `i_minRange` or > `i_maxRange`.
  - Testable: requires OHLC.

- **Stop method & TP splits**
  - Purpose: `i_slMethod` (Opposite/Midpoint), staircase stop, TP1/2/3 with qty splits.
  - Testable: can evaluate using reconstructed trades (entry/exit information).

- **One-trade-per-day enforcement**
  - Purpose: limit to single run per session (`tradeTakenToday` boolean).
  - Testable: can verify in reconstructed trades via entry timestamps.

- **Adaptive sizing / pyramiding**
  - Purpose: optional adaptive sizing rules (tested as negative hypotheses in plan).
  - Testable: partially via reconstructed trades (qty column), but full testing requires OHLC for scenario reconstruction.

- **Other components (HTF bias, liquidity sweeps, FVGs, psych rules, news filters)**
  - Purpose: context and discretionary filters referenced in docs.
  - Testable: require additional data and manual annotation; flag for future research.

---

Next actions
- Re-tag reconstructed trades against OHLC when a matching OHLC dataset is provided.
- Run component tests for VWAP, EMA, ATR, and ORB filters once OHLC is available.
- Meanwhile, run meta-analysis on reconstructed trades (entry_type, TP behavior, time-of-day) and produce an initial evidence-backed recommendation list.
