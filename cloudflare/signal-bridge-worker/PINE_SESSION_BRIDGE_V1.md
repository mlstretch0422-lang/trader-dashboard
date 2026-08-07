# Pine Session Bridge v1

Status: CODE READY FOR TRADINGVIEW COMPILE / ALERT TEST

## Purpose

`ES_ORB_Indicator_v1_2_SESSION_BRIDGE.pine` turns the current ORB indicator into a Signal Bridge session sensor without changing the v1.1 entry model.

The existing `Long Setup Ready` and `Short Setup Ready` alertconditions remain in place. The new lifecycle uses Pine `alert()` calls as a separate integration stream.

## Lifecycle events

The indicator emits structured JSON for:

- `PREMARKET` — configurable snapshot, default 07:55 ET.
- `ORB_FORMED` — after the existing default 08:00–08:15 ET ORB finishes.
- `PREOPEN` — configurable snapshot, default 09:15 ET.
- `OPEN_SNAPSHOT` — at the existing trade-window start, default 09:30 ET.
- `SETUP` — confirmed fresh breakout/retest candidate state.
- `WAIT` — candidate timeout before confirmation.
- `SESSION_CLOSE` — at the existing trade-window end, default 11:00 ET, including no-signal days.

The lifecycle records current chart price, ORB levels/range when known, VWAP/EMA context state when those filters are enabled, setup family, signal/no-signal outcome, and first ORB break classification.

## First-break handling

Realtime execution can observe whether the ORB high or low trades first.

If one historical chart bar spans both sides and order cannot be reconstructed from OHLC alone, the bridge records `BOTH_OR_SAME_BAR` rather than inventing sequence.

## Timestamp handling

Pine sends its chart epoch timestamp as `event_time`. The Worker normalizes numeric epoch milliseconds to ISO before D1 storage so the website and Discord bot share one timestamp format.

## TradingView alert configuration

After the script compiles in TradingView, create one additional alert:

- **Condition:** `ES/MES ORB Retest Indicator v1.2 SESSION BRIDGE` → `Any alert() function call`
- **Webhook URL:** `https://signal-bridge-webhook.airy-iris.workers.dev/tv-session`
- **Frequency:** controlled by the script's `alert()` calls; no custom message is required.

Keep the existing Long/Short setup alerts pointed at `/tv-alert`. The session lifecycle and trade-signal ledger remain separate by design.

## What v1.2 does not change

- Default ORB clock remains 08:00–08:15 ET.
- Default trade window remains 09:30–11:00 ET.
- Range filter remains 5–50 points.
- Displacement logic remains 0.35 ORB range or 0.75 ATR.
- Retest modes remain Breakout / Boundary / Midpoint.
- VWAP remains on by default and EMA off by default.
- One setup signal per day remains intact.

No performance claim is attached to the lifecycle layer. Its purpose is durable observation and product integration.

## Product consumers

The same D1 session record feeds:

1. Website Morning Desk and Setup Readiness.
2. Discord `/orb` and `/brief`.
3. Hosted 08:45 ET premarket desk.
4. Hosted 09:25 ET opening pulse.
5. Hosted 11:10 ET NY-AM session recap.
6. Future Strategy DNA / Session Story review.
