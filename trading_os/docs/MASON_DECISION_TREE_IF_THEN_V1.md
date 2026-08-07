# MASON DECISION TREE IF/THEN V1

Status: Draft extraction from latest live notes (2026-07-08)
Purpose: Convert discretionary language into testable logic blocks.
Scope: ES/MES intraday, one-trade-per-day funded constraints.

Architecture anchor:
- Process order is expectation-first, then observation, then execution.

Core phrase lock (user language):
- The market moves through manipulation, consolidation, and continuation in any order across Asia, London, and New York sessions.

State-model expansion (for robustness):
- The market can transition between accumulation, expansion, manipulation, consolidation, continuation, or reversal.
- These states are observations, not assumptions.
- The decision engine must classify current auction state before evaluating trade opportunities.

## 1) Non-Negotiable Operating Constraints

- Trading window for entries: 09:30 to 10:30 ET
- Hard no-new-trade cutoff: 11:00 ET
- Max trades per day: 1
- Daily strategy loss stop: 200 USD
- Primary objective: survive funded drawdown limits first, then optimize cadence

If current time > 11:00 ET, then state = NO_TRADE_DAY.
If daily realized PnL <= -200 USD, then state = LOCKOUT_DAY.
If trade_count_today >= 1, then state = LOCKOUT_DAY.

## 2) Top-Down Market Mapping (What Eyes Check First)

At approximately 09:15 ET, map context in this order:

1. 4H and 1H structure direction
2. 30m and 15m agreement or disagreement
3. Session liquidity map: Asia high/low, London high/low, prior day high/low

If 4H and 1H are aligned and 15m is not in direct conflict, then HTF_bias = ALIGNED.
If 4H and 1H conflict, then HTF_bias = MIXED and trade quality cap = B unless resolved by price behavior.

## 3) Bias Engine (Pre-open)

Long bias candidate if all true:
- Recent 4H/1H structure is bullish or in bullish continuation after retrace
- Major downside liquidity (Asia/London/prior low) is near or recently swept
- Price shows reclaim behavior back above key level(s)

Short bias candidate if all true:
- Recent 4H/1H structure is bearish or in bearish continuation after retrace
- Major upside liquidity (Asia/London/prior high) is near or recently swept
- Price shows reclaim behavior back below key level(s)

If neither long nor short candidate is true, then bias = NEUTRAL and default action = WAIT.

## 4) Sweep and Fake Sweep Definitions

Sweep definition (long context):
- Price trades into a known downside liquidity pool not revisited recently
- Pool examples: Asia low, London low, prior day low
- Sweep intent hypothesis: collect resting liquidity before continuation/reversal path

Sweep definition (short context):
- Price trades into a known upside liquidity pool not revisited recently
- Pool examples: Asia high, London high, prior day high

Fake sweep definition:
- After touching liquidity, price continues through level with significant follow-through instead of reclaim
- Operationally: closes continue beyond level by a meaningful distance and no timely reclaim appears

Test placeholder thresholds (to calibrate):
- sweep_follow_through_pts_threshold = 4.0 to 8.0 points
- reclaim_time_limit_bars_5m = 1 to 3 bars

If sweep occurs and reclaim appears within time limit, then sweep_status = VALID.
If sweep occurs and extension exceeds threshold before reclaim, then sweep_status = FAKE.

## 5) Reclaim and Continuation Expectations

Core expectation question:
"Is price doing what I expected after liquidity interaction?"

Long expectation path:
- Sweep downside liquidity
- Reclaim key reference (session low level / VWAP area / structure level)
- Hold above reclaim
- Continue toward upside liquidity target

Short expectation path:
- Sweep upside liquidity
- Reclaim down through key reference
- Hold below reclaim
- Continue toward downside liquidity target

If post-sweep behavior matches expectation path, then narrative_state = CONFIRMED.
If post-sweep behavior breaks expectation path, then narrative_state = INVALIDATED.

## 5B) Expectation Engine (Required Separation)

Rule: separate EXPECTATION from OBSERVATION in every setup.

Long setup template:
- EXPECTATION:
	- HTF context remains bullish.
	- Price can retrace into known downside liquidity (Asia low, London low, ORB low, previous session low).
	- After sweep, bearish continuation should fail.
	- Price should reclaim swept area and rotate toward higher liquidity.
- OBSERVATION CHECK:
	- Did price sweep a mapped downside pool?
	- Did continuation lower fail (loss of bearish follow-through)?
	- Did reclaim occur within tested window?
	- Did bullish structure reassert?
- DECISION:
	- If all observation checks are true: continue to execution filters.
	- If acceptance remains below the swept level with strong continuation lower: invalidate long bias.

Short setup template:
- EXPECTATION:
	- HTF context remains bearish.
	- Price can retrace into known upside liquidity (Asia high, London high, ORB high, previous session high).
	- After sweep, bullish continuation should fail.
	- Price should reclaim down and rotate toward lower liquidity.
- OBSERVATION CHECK:
	- Did price sweep a mapped upside pool?
	- Did continuation higher fail (loss of bullish follow-through)?
	- Did reclaim-down occur within tested window?
	- Did bearish structure reassert?
- DECISION:
	- If all observation checks are true: continue to execution filters.
	- If acceptance remains above the swept level with strong continuation higher: invalidate short bias.

Canonical clarity sentence:
- A liquidity sweep is not the trade. The trade is the market response to the sweep, aligned with HTF auction direction.

## 6) Clean vs Choppy Regime

Chop cues from notes:
- Price fails to leave ORB area with intent
- Repeated back-and-forth around ORB without directional expansion
- Low volatility / weak displacement after open

Operational placeholders (to calibrate):
- minimum_orb_escape_pts = 4.0 to 6.0 points
- maximum_chop_flips_5m = 3 direction flips within 20 to 30 minutes

Canonical proxy from existing notes:
- If ORB midpoint is crossed 6 or more times within 1 hour, classify as CHOP environment.

If ORB escape < minimum_orb_escape_pts and flip count exceeds limit, then regime = CHOP.
If regime = CHOP by 10:00 ET, then default action = SKIP unless a high-confidence narrative reset occurs.

If midpoint_crosses_1h >= 6, then regime = CHOP.

## 7) News/Unnatural Action Invalidation

Immediate invalidation conditions:
- Very large abnormal candles relative to local baseline
- Event-like behavior (news, war headline, shock move)
- Price action cannot be reconciled with mapped HTF structure and session levels

Operational placeholders (to calibrate):
- abnormal_body_multiple = 2.5x to 3.5x recent 20-bar median body
- abnormal_range_multiple = 2.5x to 3.5x recent 20-bar median range

If abnormal action trigger is true, then bias_state = INVALID and action = STAND_DOWN until structure re-forms.

## 8) Indicator Role (Confirmation, Not Primary Driver)

EMA and VWAP are confirmation layers, not primary thesis.

If narrative_state != CONFIRMED, then EMA/VWAP alignment cannot force an entry.
If narrative_state = CONFIRMED, then EMA/VWAP alignment upgrades setup quality score.

## 9) Setup Grading

A+ setup if all true:
- HTF alignment present (or clearly resolved)
- Liquidity interaction is clear (sweep + valid reclaim)
- Price behavior matches expected continuation path
- Time quality is strong (near open and active conditions)
- Regime is not chop

B setup if true:
- Most but not all A+ conditions hold
- One moderate conflict exists but no hard invalidation

No Trade if any true:
- Hard risk/time lockout triggered
- Regime = CHOP and no reset
- Narrative invalidated
- Abnormal event behavior

## 10) Test Conversion Checklist (Mechanical Build Order)

1. Encode mapping features: session levels and HTF direction flags
2. Encode sweep/fake-sweep event states with calibrated thresholds
3. Encode expectation-path state machine (expected vs invalidated)
4. Encode manipulation/consolidation/continuation state labels across Asia/London/NY
5. Encode chop detector and no-trade gate
6. Add EMA/VWAP as quality modifiers only
7. Backtest modules independently, then combined
8. Reject any candidate with trades < 20 or monthly_pass_rate = 0 over evaluation horizon

## 11) Missing Inputs To Finalize V2

- Exact measurable proxies for manipulation/consolidation/continuation states
- Exact point thresholds for "significant extension" and "valid reclaim speed"
- Exact A+ vs B scoring weights

## 12) Canonical MSS Definition (Pulled From Existing Project Notes)

Market Structure Shift (MSS) / ChoCh:
- A change in highs/lows pattern that implies directional control shift.

Bull MSS:
- Prior local pattern was lower highs and lower lows.
- Shift condition: previous low is not broken (higher low forms).
- Confirmation trigger candidate: break of swing high after higher low.

Bear MSS:
- Prior local pattern was higher highs and higher lows.
- Shift condition: previous high is not broken (lower high forms).
- Confirmation trigger candidate: break of swing low after lower high.

Integration rule:
- If ORB break direction aligns with MSS direction, setup quality increases.
- If ORB break direction conflicts with MSS direction, setup quality decreases or setup is filtered.

Until these are filled, this document is a strict draft extraction, not a final production rulebook.
