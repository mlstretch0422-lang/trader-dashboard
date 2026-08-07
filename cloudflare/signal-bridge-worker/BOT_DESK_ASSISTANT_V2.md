# Signal Bridge Bot Desk Assistant v2

Status: implementation complete; deploy + D1 migration required.

## Role

Signal Bridge is one app/bot. Discord is the fast field-assistant layer while the website is the durable memory/intelligence layer.

The bot reads Signal Bridge state. It does not create independent trading logic or invent market state.

## Interactive commands

- `/status` — Worker, ledgers, journal/member access, scheduled desk, calendar/headline freshness, latest MES session.
- `/orb` — latest stored ORB plus current lifecycle state.
- `/brief` — current Session Story and Setup Readiness. Readiness is defined-condition completion, not win probability.
- `/news` — verified economic-calendar state plus cached market headlines. Calendar fails closed when unavailable.
- journal/member commands remain separate from the intelligence commands.

Intelligence commands use branded Discord embeds and deferred interaction responses so database/provider work does not race Discord's response deadline.

## Scheduled desk

Cloudflare Cron remains hosted independently of the local Mac.

Market/headline cache refresh:
- every 15 minutes

Desk dispatch cron:
- every five minutes during a broad UTC window on weekdays
- `bot_scheduler.js` converts scheduled time to `America/New_York`
- messages only dispatch at exact ET windows

Current desk windows:
- **08:45 ET** — Pre-market Desk: session brief + news/calendar state.
- **09:25 ET** — Opening Bell Pulse: only posts when session data exists.
- **11:05 ET** — NY-AM Session Recap: only posts when session data exists.

A durable `bot_dispatch_log` record prevents duplicate scheduled posts if Cloudflare retries an invocation or overlapping cron activity occurs.

## Discord routing

Scheduled intelligence posts use:

1. `DISCORD_INTELLIGENCE_WEBHOOK_URL` when configured.
2. Existing `DISCORD_WEBHOOK_URL` as fallback.

This allows the same Signal Bridge app to later route intelligence into a dedicated channel without changing the journal/signal backend.

## Data honesty

- Missing ORB/session state returns unavailable/waiting, not estimated levels.
- Missing calendar provider returns unavailable/stale, never "no red news."
- Setup Readiness is a transparent count of stored conditions: ORB, bias, setup, actionable side, and target.
- Scheduled open/recap messages skip when no real session lifecycle exists.

## Next dependency: Pine lifecycle output

The hosted intelligence layer is ready for the indicator to send:

`PREMARKET -> ORB_FORMED -> PREOPEN -> OPEN_SNAPSHOT -> SETUP / WAIT -> SESSION_CLOSE`

Once those events are emitted by the Pine indicator, the website Morning Desk and Discord assistant will read the same durable session object.
