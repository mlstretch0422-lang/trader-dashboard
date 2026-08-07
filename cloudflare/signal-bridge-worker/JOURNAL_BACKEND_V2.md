# Signal Bridge Journal Backend v2

## Why this exists

The first Discord journal layer proved capture into D1, but publishing depended too heavily on matching a Discord message back to a stored row. Journal Backend v2 moves publication and review controls onto the journal record itself.

The journal row is now the durable source of truth. Discord and the website are clients of that record.

## Current journal states

- `PRIVATE` + `RAW` — default Discord capture.
- `PRIVATE` + `NORMALIZED` — derived fields may be added without exposing the record publicly.
- `PRIVATE` + `REVIEWED` — reviewed but still private.
- `PUBLISHED` + `REVIEWED` — intentionally visible through the public `/journal` feed.

`raw_text`, Discord provenance, and source references are intentionally treated as the immutable source record by the admin API. Normalized/derived fields can change around that source record.

## Discord controls

### `/journal`

Creates a journal record and returns a short journal ID in the receipt.

### `Capture to Journal`

Captures a normal Discord message privately and returns the stored journal ID.

### `/journal-inbox`

Returns an ephemeral list of the invoking Discord user's recent journal records. It can show private, published, or all records and includes short journal IDs plus chart links when present.

### `/journal-publish id:<ID>`

Server-manager-only. Publishes the exact stored journal record by full ID or unique ID prefix. This path does not depend on resolving the original Discord message again.

### `/journal-private id:<ID>`

Server-manager-only. Moves a published record back to private.

### `Publish to Journal`

The message context action remains as a convenience path. If the message is already captured, it promotes that row. If it is not stored yet, it creates a published record. The ID-based commands remain the durable fallback and review workflow.

## Authenticated management API

The hosted Worker exposes a protected management surface under `/journal-admin`.

Authentication uses `JOURNAL_ADMIN_TOKEN` when configured, otherwise the existing `JOURNAL_INGEST_TOKEN` acts as the admin credential. No token is exposed to the static website.

### List records

`GET /journal-admin`

Supported filters:

- `visibility=PRIVATE|PUBLISHED`
- `review_status=RAW|NORMALIZED|REVIEWED`
- `author=<discord user id>`
- `symbol=<symbol>`
- `limit=1..100`

Unlike the public journal feed, this protected response includes the private source/provenance fields required for review.

### Read one record

`GET /journal-admin/<journal-id-or-unique-prefix>`

### Normalize / edit derived fields

`PATCH /journal-admin/<journal-id-or-unique-prefix>`

Mutable fields:

- symbol
- side
- setup
- strategy
- title
- summary
- result
- pnl
- rr
- tags
- signal_event_id
- image_url
- review_status
- visibility

The admin API intentionally does not edit `raw_text` or Discord provenance.

### Publish

`POST /journal-admin/<journal-id-or-unique-prefix>/publish`

Sets `visibility=PUBLISHED` and `review_status=REVIEWED`.

### Return to private

`POST /journal-admin/<journal-id-or-unique-prefix>/private`

Returns the record to `PRIVATE` without deleting or rewriting its source history.

## Public website boundary

`GET /journal` remains the only unauthenticated journal feed and returns `PUBLISHED` entries only.

The current GitHub Pages website must not fetch `/journal-admin` because a static public frontend has no safe place to keep an admin/member credential. The next web phase should use Discord OAuth / signed sessions before private journal records are rendered on the website.

## Next member layer

1. Discord OAuth identity.
2. Signal Bridge user record linked to Discord user ID.
3. Signed session cookie.
4. Private `GET /me/journal` route scoped to the authenticated owner.
5. Durable media copy for Discord screenshots rather than relying on attachment URLs forever.
6. Strategy/version and signal-event linking during review.
7. Member journal analytics from normalized records.
