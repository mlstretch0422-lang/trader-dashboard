# Signal Bridge Session Intelligence v1

## Purpose

The live trade-signal ledger and the market-session intelligence ledger are separate on purpose.

- `signal_events` answers: **what trade/signal event fired?**
- `session_events` answers: **what did the market/session do around the strategy even if no trade was taken?**

That separation lets Signal Bridge learn from no-trade days, ORB behavior, setup development, and post-session outcomes without pretending every observation was a trade.

## Hosted routes

### TradingView lifecycle ingest

`POST /tv-session`

This route uses the same TradingView source-IP allowlist as the live alert bridge. It is intended for Pine lifecycle alerts running on TradingView's servers.

### Authenticated system test

`POST /session-test`

Uses `SIGNAL_BRIDGE_TEST_TOKEN`. The Worker forces the stored stage to `TEST` so infrastructure checks never look like real session evidence.

### Public session event history

`GET /session-events`

Optional filters:

- `symbol=MES`
- `session_date=YYYY-MM-DD`
- `stage=ORB_FORMED`
- `limit=1..100`

`TEST` events are excluded from the public response.

### Session summary

`GET /session-summary?symbol=MES`

Returns the latest recorded session date for the requested symbol, the latest ORB record, latest session state, and chronological lifecycle events.

## Lifecycle stages

### `PREMARKET`

Snapshot before the active morning sequence. Intended fields can include price, HTF/session bias, mapped liquidity, and a short note.

### `ORB_FORMED`

The opening range has frozen. The preferred payload contains:

- `orb_high`
- `orb_low`
- `orb_mid`
- `range_points`
- timeframe
- optional bias/note

The Worker derives midpoint/range size when high and low are provided but the derived fields are omitted.

### `PREOPEN`

State after the ORB and before the NY cash open. Useful for recording which side was swept/broken, where price sits relative to the range, and whether a candidate setup is developing.

### `OPEN_SNAPSHOT`

NY-open state. Intended to record participation/acceptance context without claiming a trade.

### `SETUP`

A strategy setup has reached a defined ready/near-ready state. This can include side, setup name, target, bias, price, and the mechanical reason.

### `WAIT`

The system intentionally has no qualifying trade yet, or a watched setup failed to confirm. This is a useful outcome and should be stored rather than discarded.

### `SESSION_CLOSE`

End-of-window summary. Intended fields include final outcome, which ORB side traded first/ultimately held, target travel, pass reason, and any session-level learning labels.

### `TEST`

Infrastructure-only event class. Never used as strategy evidence.

## Example ORB lifecycle payload

```json
{
  "symbol": "MES",
  "stage": "ORB_FORMED",
  "strategy": "Mason ORB",
  "timeframe": "1m",
  "orb_high": 6000.25,
  "orb_low": 5992.75,
  "bias": "HTF bullish",
  "note": "8:00-8:15 ET opening range frozen",
  "time": "{{timenow}}"
}
```

The Worker derives `orb_mid` and `range_points` if they are not supplied.

## Example setup payload

```json
{
  "symbol": "MES",
  "stage": "SETUP",
  "side": "LONG",
  "price": "{{close}}",
  "strategy": "Mason ORB",
  "setup": "Downside sweep + ORB reclaim",
  "bias": "HTF bullish",
  "target": "ORB high / next mapped liquidity",
  "note": "Retest confirmed after downside liquidity sweep",
  "time": "{{timenow}}"
}
```

## Example post-session payload

```json
{
  "symbol": "MES",
  "stage": "SESSION_CLOSE",
  "strategy": "Mason ORB",
  "outcome": "ORB low swept first; midpoint reclaimed; ORB high reached",
  "note": "No qualifying entry recorded",
  "time": "{{timenow}}"
}
```

## Discord commands

### `/status`

Shows hosted Worker, signal ledger, session ledger, journal capture, and journal-admin configuration status.

### `/orb [symbol]`

Reads the latest stored `ORB_FORMED` record. It does not calculate or invent an ORB inside Discord.

### `/brief [symbol]`

Builds a concise session summary from the stored lifecycle sequence. If Pine has not emitted session events yet, the command says no session lifecycle has been recorded instead of fabricating market context.

## Pine integration rule

The Worker/bot owns storage, delivery, and summaries. Pine owns chart-derived market state.

Signal Bridge should not guess an ORB, sweep, reclaim, or setup from a generic quote when the strategy indicator can emit the exact state that was visible on the chart. This keeps Discord, the website, and later research synchronized to the same mechanical definitions used by the indicator.

## Evidence rule

A stored session lifecycle event is a market/process record. It becomes useful forward evidence, but it is not automatically proof that a strategy component has statistical edge. Backtest, attribution, replay/paper-forward, funded, and live evidence remain separate.
