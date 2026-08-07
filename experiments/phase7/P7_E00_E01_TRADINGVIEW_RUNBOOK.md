# Phase 7 TradingView Runbook — E00 Compile/Sanity + E01 Entry Mode

This is the exact manual run sequence for the current attribution harness.

Research script:

`pine/research/ES_MES_ORB_Attribution_Strategy_v1_3.pine`

Do not use the older v1.1 or v1.2 files for this run.

---

## P7-E00 — Compile and sanity check

### Chart

- Symbol: `CME_MINI:ES1!`
- Timeframe: `15m`
- Chart time zone display can be anything; the script internally uses `America/New_York`.

### Pine Editor

1. Open Pine Editor.
2. Create a new blank strategy.
3. Paste the complete contents of `pine/research/ES_MES_ORB_Attribution_Strategy_v1_3.pine`.
4. Save as `Signal Bridge P7 Attribution v1.3`.
5. Click **Add to chart**.
6. Stop immediately if TradingView shows a compiler error or warning that changes strategy behavior. Capture the exact message.

### Expected dashboard state

On `CME_MINI:ES1!` / `15m`:

- `Environment` = `PASS`
- `Chart` = `ES / 15`
- `Entry Window` = `0930-1030`
- `Force Flat` = `1100`
- `VWAP / EMA` = `- / -`
- `Displacement` = `Off: PASS`
- `Range Gate` = `OFF`

### Locked historical window

The script itself limits entries to:

- Start: April 1, 2025
- End: February 27, 2026 exclusive

Do not change those dates for P7-E01.

### Strategy properties that must remain unchanged

- Initial capital: `$50,000`
- Order size: `1 contract`
- Commission model: `cash per contract`
- Commission: `$1.20 per contract per executed order`
- Pine slippage setting: `2 ticks`
- Expected ES/MES minimum tick: `0.25 point`
- Interpreted slippage: about `0.50 point per affected fill`
- Process orders on close: `enabled by code`
- Pyramiding: `0`

Do not manually override commission, slippage, order size, or fill behavior in Strategy Properties.

### Sanity checks before collecting results

Confirm visually on several historical trades:

1. There is never more than one entry in a New York calendar day.
2. `Boundary` and `Midpoint` modes do not count the breakout bar itself as the retest.
3. Long setup invalidates after a close below ORB low; short setup invalidates after a close above ORB high.
4. Any still-open trade is closed when the analyzed bar closes at 11:00 New York.
5. Stop and target orders are attached to the entry immediately rather than appearing a full bar later.
6. No entries appear outside the locked test dates.

If any check fails, P7-E01 is blocked until code is corrected.

---

# P7-E01 — Entry Mode Attribution

Question:

> Does requiring a retest improve expectancy/drawdown versus immediate breakout, and does midpoint outperform boundary retest?

Only **Entry Mode** changes. Everything else remains frozen.

## Frozen settings

### Experiment Lock

- Enforce Expected Symbol Root + Timeframe: `ON`
- Expected Symbol Root: `ES`
- Expected Timeframe: `15`
- Historical Test Start: default
- Historical Test End: default

### Time Settings

- Timezone: `America/New_York`
- ORB Start: `0800`
- ORB End: `0815`
- Trade Start: `0930`
- No New Entries After: `1030`
- Force Flat At: `1100`

### Entry Attribution

- Enable Longs: `ON`
- Enable Shorts: `ON`
- Retest Timeout Bars: `60`
- Invalidate On Close Through Opposite ORB Side: `ON`

### Filter Attribution

- Displacement Mode: `Off`
- Use VWAP Alignment: `OFF`
- Use EMA Alignment: `OFF`
- Use ORB Range Filter: `OFF`

The inactive threshold values remain untouched:

- Min Body % of ORB Range: `0.35`
- Min Body × ATR: `0.75`
- ATR Length: `14`
- EMA Length: `50`
- Min ORB Range Points: `5`
- Max ORB Range Points: `50`

### Risk Attribution

- Stop Method: `Opposite`
- Fixed Stop Points: `10` (inactive while Stop Method = Opposite)
- Single Target R: `2.0`
- Maximum Allowed Stop Points: `40`

---

## Run 1 — Immediate Breakout

Change only:

`Entry Mode = Breakout`

Record/export:

- Net Profit
- Total Trades
- Percent Profitable / Win Rate
- Profit Factor
- Max Drawdown
- Average Trade
- Average Winning Trade
- Average Losing Trade
- Largest Losing Trade
- full **List of Trades** CSV

Result ID:

`P7-E01_immediate_breakout_ES1_15m_2025-04-01_2026-02-26`

---

## Run 2 — Boundary Retest

Change only:

`Entry Mode = Boundary`

Record/export the exact same fields.

Result ID:

`P7-E01_boundary_retest_ES1_15m_2025-04-01_2026-02-26`

---

## Run 3 — Midpoint Retest

Change only:

`Entry Mode = Midpoint`

Record/export the exact same fields.

Result ID:

`P7-E01_midpoint_retest_ES1_15m_2025-04-01_2026-02-26`

---

# Do not optimize during E01

Do not change:

- ORB time
- stop method
- target R
- max stop
- displacement thresholds
- VWAP
- EMA
- range gate
- commission
- slippage
- date range
- symbol
- timeframe

A bad result is useful data. Do not tune a losing variant mid-experiment.

---

# Decision rule

Do not pick the variant with the largest net profit automatically.

Primary comparison:

1. Profit factor
2. Expectancy / average trade
3. Max drawdown
4. Worst losing sequence
5. Trade count / sample retention

A retest variant is worth carrying forward only if it improves trade quality or drawdown without achieving that result merely by deleting most of the sample.

No E01 winner is promoted to VERIFIED. The winner becomes the frozen candidate for E02 and later holdout validation.

---

# Handoff

Upload the three TradingView exports to the project/chat without renaming their original files if possible. The comparison will be committed under a dedicated Phase 7 result directory with the exact source commit and settings used.
