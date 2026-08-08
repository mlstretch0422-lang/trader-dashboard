# Pine Visual Stack v1

Status: STAGED · TRADINGVIEW COMPILE REQUIRED

Primary file:

`ES_ORB_Indicator_v1_3_VISUAL_STACK.pine`

## Purpose

v1.3 is the first dedicated **professional chart presentation pass** over the merged v1.2 Session Bridge.

It does not optimize the trading model. The objective is to make the indicator useful and shareable as an execution-support tool while preserving the existing v1.2 signal/lifecycle behavior underneath it.

## Preserved strategy/integration behavior

- Pine v6
- ORB default 08:00–08:15 ET
- trade window default 09:30–11:00 ET
- displacement = 0.35 ORB range OR 0.75 ATR
- Midpoint retest default
- retest timeout 60 bars
- VWAP strategy filter ON by default
- EMA strategy filter OFF by default
- range filter 5–50 points
- one signal per day
- `Long Setup Ready` and `Short Setup Ready` alertconditions
- PREMARKET / ORB_FORMED / PREOPEN / OPEN_SNAPSHOT / SETUP / WAIT / SESSION_CLOSE lifecycle output

Strategy DNA stays on `mason-orb-v1.2-session-bridge` because the v1.3 work is visual/integration-only. `indicator_version` reports `1.3-visual-stack`.

## Visual modules added

### Native opening range

- low-opacity range box
- ORH / ORM / ORL plots
- configurable history count
- native drawing objects instead of dense labels

### Liquidity/context references

- previous-day high/low
- overnight high/low
- optional previous completed 1H/4H highs/lows
- VWAP display independent of whether VWAP is being used as a strategy filter
- optional EMA 20 / 50 / 100 / 200 display lines

All of these are visual context. Adding a plot does not make that component a validated entry filter.

### Reference session boxes

Optional custom Asia/London boxes use Pine session inputs and are **OFF by default**.

The default visual windows are editable reference windows only. They are not promoted into strategy rules because the project's session/ORB timing research still contains competing definitions.

### Decision panel

The new panel shows transparent module state rather than a hidden confidence score:

- ORB state
- range
- range filter
- first ORB break
- trade window
- strategy context
- setup
- retest
- desk state
- lifecycle connection

## Visual design basis

The project visual specification calls for:

- price remaining the visual star;
- low-opacity range/session boxes;
- native Pine `box` / `line` / plot objects;
- limited drawing history;
- sparse fixed signal markers;
- a small custom decision panel;
- indicator logic separated from strategy/backtest logic.

TradingView's Pine documentation supports using boxes/lines for calculated ranges and `xloc.bar_time` for time-anchored drawings. Time-based session strings with `time()` are used for the optional context boxes.

## Compile gate

GitHub CI can verify the source contract but cannot compile Pine on TradingView's servers.

Do not replace the current v1.1/v1.2 chart source until this file has compiled successfully in TradingView.

After compile, the visual inspection should focus on:

1. ORB box/history behavior.
2. Overnight and previous-day levels.
3. mobile/chart readability and clutter.
4. session boxes only if intentionally enabled.
5. decision panel size/placement.
6. lifecycle alerts still appearing under `Any alert() function call`.
