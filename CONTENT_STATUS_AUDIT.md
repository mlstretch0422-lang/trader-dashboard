# Content Status Audit

This audit separates accepted project facts from hypotheses and implementation ideas.

## Status definitions

- **VERIFIED** — explicitly supported by project records or accepted system rules.
- **TESTING** — implemented or being evaluated, but not proven enough to present as settled.
- **UNTESTED** — idea, toggle, or confluence with no completed validation evidence in the reviewed source.
- **RETIRED** — rejected, deprecated, or replaced.

## VERIFIED

| Item | Status basis |
|---|---|
| Primary market is MES / ES | Repeated throughout the project files and Pine scripts. |
| ORB reference window is 08:00–08:15 New York time | Implemented in the indicator and documented in the project direction. |
| New-entry window begins at 09:30 and stops no later than 10:30 for the primary model | Explicitly documented in the mechanical research brief. |
| Force-flat by 11:00 is part of the primary operating model | Explicitly documented in the mechanical research brief. |
| Maximum one planned trade per day is the primary model | Explicitly documented in the mechanical research brief. |
| The strategy should be evaluated as a full system: bias → setup → trigger → risk → execution → validation | Explicit architecture in the mechanical research brief. |
| Backtests must avoid lookahead bias and unrealistic fills | Explicit validation requirement in the mechanical research brief. |
| Historical, replay, paper, and live performance must remain separate | Project governance requirement; no blended performance claims. |

## TESTING

| Item | Why it is not VERIFIED |
|---|---|
| ORB breakout → retest → continuation sequence in `ES_ORB_Indicator_v1_1_FIXED.txt` | It is implemented, but implementation is not proof of edge. |
| ORB midpoint retest as the default retest mode | Present in code as a default input, but the reviewed source does not establish it as universally superior. |
| Displacement thresholds of 35% of ORB range or 0.75× ATR | Present as code parameters; no accepted validation record reviewed yet. |
| ORB range filter of 5–50 points | Implemented as defaults; requires instrument- and regime-specific evidence. |
| VWAP alignment enabled by default | Implemented as a filter, but still requires isolated attribution. |
| EMA alignment filter | Present as an optional toggle, not an accepted edge component. |
| Retest timeout of 60 bars | Operational parameter only; not validated by the reviewed source. |
| Liquidity sweep → reclaim/rejection → confirmation model | Current preferred research direction, but the research brief itself is design guidance rather than completed proof. |
| Trailing-drawdown survival ranking | Correct evaluation priority for funded-mode research, but strategy candidates still need actual out-of-sample evidence. |

## UNTESTED

The following are listed in the research brief as candidate confirmations, levels, filters, or optimizer toggles. They must not appear on the premium website as official rules unless a separate accepted test record supports them.

- EMA alignment as a required rule
- Volume confirmation
- Red-news proximity filter implementation
- FVG requirement
- London level requirement
- Premarket level requirement
- Previous-day direction filter
- Previous-day high/low/close as mandatory setup levels
- Engulfing-candle requirement
- Rejection-wick requirement as a universal trigger
- Minimum body-percent thresholds beyond the current test parameters
- Minimum close-strength thresholds
- Breakeven logic
- Trailing-stop logic
- Partial exits
- A second trade after a loss
- Adaptive contract scaling
- Any confluence score presented as proven

## RETIRED / REJECTED UNTIL RE-EARNED

| Item | Reason |
|---|---|
| Blind ORB breakout entry | The project direction explicitly rejects treating an ORB break as an automatic entry. |
| Any rule described only as “looks bullish,” “momentum seems strong,” or a “good-looking setup” | Not mechanical or testable. |
| Ranking candidates by net profit alone | Explicitly rejected by the research framework. |
| Presenting low-sample optimizer winners as production-ready | Fails evidence and robustness standards. |
| Combining backtest, paper, and live metrics into one performance number | Misleading and prohibited by project governance. |

## Code audit: `ES_ORB_Indicator_v1_1_FIXED.txt`

### What the script currently does

- Builds an 08:00–08:15 New York ORB.
- Allows a 09:30–11:00 trade-seeking window.
- Applies ORB-range, displacement, VWAP, and optional EMA gates.
- Arms a long or short after a close beyond the ORB.
- Waits for a selected retest mode.
- Emits at most one signal per day.
- Displays ORB levels and a dashboard.

### Important limitations

1. The file name says `FIXED`, but that is a code-version label, not evidence that the trading logic is validated.
2. The code models a breakout-retest continuation system, while the research brief says the preferred direction is liquidity sweep → reclaim/rejection → confirmation.
3. The VWAP, EMA, displacement, range, and timeout defaults are research parameters, not premium-site facts.
4. The indicator does not by itself establish fill quality, slippage, commissions, drawdown survival, or out-of-sample robustness.
5. A TradingView signal should be labeled as a research signal until strategy tests and replay evidence support promotion.

## Website rules from this audit

- Premium pages may describe VERIFIED items as current system rules.
- TESTING items must display a visible `Testing` badge and link to evidence.
- UNTESTED items belong only in the Research Lab.
- RETIRED items belong in version history, not the active Trade Bible.
- Every metric must state its source, sample size, date range, and test type.
- No indicator or strategy may be marketed as validated solely because it compiles or appears on a chart.

## Next evidence needed

1. Full inventory of optimizer outputs and accepted/rejected candidates.
2. Isolated attribution for VWAP, EMA, ORB range, displacement, and retest mode.
3. Walk-forward and final holdout results.
4. Paper/replay sample using the exact coded rules.
5. Reconciliation between the current Pine implementation and the preferred liquidity-sweep model.
