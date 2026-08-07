# Signal Bridge Journal Intelligence Setup

## Goal

Create a durable, private-first journal ledger that can eventually receive short trade journal posts from Discord, preserve the untouched source note, normalize it into structured trade fields, link it to Signal Bridge events, and selectively publish reviewed educational entries to the Premium OS.

## Architecture

Target flow:

`Discord trade-journal post -> Signal Bridge bot / capture adapter -> POST /journal -> D1 private ledger -> AI normalization -> review -> PUBLISHED -> Premium OS /journal.html`

Current repository work provides the D1 schema, authenticated ingest endpoint, published read endpoint, and Premium OS page. The Discord reader/bot and AI normalizer are separate future integrations.

## Privacy boundary

The current GitHub Pages beta is publicly reachable. Therefore:

- new journal rows default to `visibility=PRIVATE`;
- public `GET /journal` returns only `PUBLISHED` rows;
- `source_ref` is stored for provenance but is never returned by the public journal endpoint;
- the raw Discord capture should not be automatically published;
- future member authentication can replace this public-beta publication boundary without changing the underlying journal schema.

## D1 migration

`migrations/0002_journal_entries.sql` adds `journal_entries` with fields for:

- execution: time, symbol, side, result, P&L, R multiple;
- strategy context: strategy, setup, tags, linked Signal Bridge event;
- provenance: raw text, source, private source reference, optional image URL;
- learning workflow: summary, visibility, review status.

Apply all remote migrations with:

```bash
npx -y wrangler@latest d1 migrations apply DB \
  --remote \
  --config cloudflare/signal-bridge-worker/wrangler.toml
```

## Journal ingest secret

Generate a dedicated token locally and store it only in `.env.local` and Cloudflare Worker secrets. Do not reuse the public TradingView payload and do not commit the token.

Expected local variable:

```text
JOURNAL_INGEST_TOKEN=<private random token>
```

## API

Public read:

```text
GET /journal?limit=25
GET /journal?symbol=MES
GET /journal?result=WIN
GET /journal?setup=ORB%20retest
```

Authenticated ingest:

```text
POST /journal
Authorization: Bearer <JOURNAL_INGEST_TOKEN>
Content-Type: application/json
```

Minimum payload:

```json
{
  "source": "discord",
  "raw_text": "Original short-form journal note"
}
```

A richer normalized payload may include:

```json
{
  "source": "discord",
  "journal_time": "2026-08-07T13:30:00-04:00",
  "symbol": "MES",
  "side": "LONG",
  "strategy": "Mason ORB",
  "setup": "ORB retest",
  "result": "WIN",
  "pnl": 125.0,
  "rr": 2.1,
  "tags": ["retest", "vwap", "morning"],
  "signal_event_id": "optional Signal Bridge event UUID",
  "image_url": "optional future screenshot URL",
  "summary": "Reviewed learning summary",
  "review_status": "REVIEWED",
  "visibility": "PUBLISHED",
  "raw_text": "Original journal note preserved unchanged"
}
```

## Evidence boundary

A journal entry documents execution and review. It does not by itself prove that a setup, filter, or strategy has statistical edge. Journal observations can generate hypotheses and forward evidence, but controlled attribution remains separate.
