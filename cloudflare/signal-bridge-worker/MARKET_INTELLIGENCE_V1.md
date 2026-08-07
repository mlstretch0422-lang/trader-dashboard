# Signal Bridge Market Intelligence v1

## Purpose

Signal Bridge keeps **economic-calendar risk** and **market headlines** separate.

- Economic-calendar data is intended to answer: **what scheduled U.S. macro releases are coming, and what were the reported/forecast/previous values?**
- Headlines are informational context only and answer: **what market stories are currently circulating?**

A headline feed must never silently substitute for an economic calendar.

## Hosted refresh

Cloudflare Worker Cron refreshes market intelligence every 15 minutes. `/news refresh:true` can also request a fresh pull before the bot replies.

The local Mac is not required.

## Economic calendar provider

The production provider adapter is built for **Trading Economics**.

Official API documentation used by the implementation:

- Authentication: https://docs.tradingeconomics.com/get_started/authentication/
- Calendar by country / importance: https://docs.tradingeconomics.com/economic_calendar/country/
- Calendar schema: https://docs.tradingeconomics.com/economic_calendar/schema/
- Point-in-time calendar data for later backtest research: https://docs.tradingeconomics.com/economic_calendar/point-in-time/

The provider requires a paid API plan/key. Signal Bridge reads the optional Worker secret:

`TRADING_ECONOMICS_API_KEY`

Until that secret is configured, the calendar state is explicitly `UNAVAILABLE`.

**Fail-closed rule:** missing, stale, or failed calendar data must never be translated into “no red news” or “calendar clear.”

The current adapter requests high-importance (`importance=3`) United States calendar events for today and tomorrow and stores the provider payload plus normalized fields including:

- event time
- event/category
- importance
- actual
- previous
- consensus forecast
- Trading Economics forecast
- source/source URL
- provider update timestamp

## Headlines

The initial informational headline adapter uses Yahoo Finance search for `SPY`. It is deliberately stored in a separate `market_headlines` table and exposed as a separate section in `/news`.

Headline availability has no effect on economic-calendar status.

## D1 tables

Migration `0006_market_intelligence.sql` adds:

- `market_intelligence_runs` — provider refresh state and errors
- `economic_calendar_events` — normalized scheduled/released macro events
- `market_headlines` — informational headline cache

Provider errors are stored as compact codes; credentials are never persisted.

## Hosted routes

### `GET /market-intelligence`

Public read-only summary of current provider state, cached upcoming calendar events, and recent headlines.

### `POST /market-intelligence/refresh`

Authenticated maintenance route using `SIGNAL_BRIDGE_TEST_TOKEN`. Refreshes the configured providers immediately.

### `/news`

Discord command that returns:

1. high-impact U.S. economic-calendar context, or explicit `UNAVAILABLE` state;
2. recent market headlines when available;
3. an update timestamp.

The command uses a deferred Discord interaction so provider/D1 work cannot lose the interaction simply because it took more than the initial acknowledgement window.

## Strategy-specific red-news rule

Market Intelligence v1 intentionally does **not** hard-code a “do not trade X minutes before/after news” rule. That rule belongs to the strategy configuration/research layer and still needs to be defined and tested.

The intelligence layer's job is to provide accurate event state. The strategy layer decides what that event state means for execution.

## Later research use

Trading Economics documents point-in-time calendar retrieval, which can preserve what forecasts/values were actually available at a historical moment. That is the preferred direction when calendar filters are eventually backtested so revised data does not leak into historical decisions.
