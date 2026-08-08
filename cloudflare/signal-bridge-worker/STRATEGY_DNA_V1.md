# Signal Bridge Strategy DNA v1

Status: BACKEND CORE IMPLEMENTED · DEPLOY/MIGRATION REQUIRED

## Product job

Strategy DNA is the durable version history behind Signal Bridge. It exists so the system can answer a question ordinary trade journals usually cannot answer cleanly:

> Which exact strategy version, indicator version, settings, and rule set produced this session evidence?

A member-facing Strategy Lab can later sit on top of this data without inventing a new backend.

## Data model

### strategy_profiles

The durable identity of a strategy.

Examples:
- Mason ORB
- a future member-owned strategy

Ownership is explicit through `owner_type` and optional `owner_discord_id`.

### strategy_versions

A versioned snapshot containing:

- version label
- status
- evidence stage
- parent version
- rules JSON
- indicator name/version
- indicator configuration JSON
- change note
- current-version flag

Evidence stage uses the project taxonomy:

`PROJECT_RULE -> IMPLEMENTED -> BACKTESTED -> ISOLATED_ATTRIBUTION -> WALK_FORWARD -> PAPER_FORWARD -> LIVE`

The stage describes evidence state; it is not a profitability label.

### strategy_observations

Links a strategy version to actual evidence objects:

- session event
- signal event
- journal entry
- outcome
- note
- structured metadata

This is the future comparison layer for questions such as:

> What changed after v1.7 versus v1.6 across forward sessions?

## Mason ORB seed

Migration 0008 seeds:

- profile: `strategy-mason-orb`
- version: `mason-orb-v1.2-session-bridge`
- evidence stage: `IMPLEMENTED`
- status: `STAGED`

The version records the locked v1.2 integration defaults and explicitly states that it adds lifecycle data capture while preserving the v1.1 signal logic.

A D1 trigger automatically attaches session events produced by the exact v1.2 Session Bridge strategy label to this Strategy DNA version. That means the first real Pine lifecycle event can enter the Strategy DNA observation ledger without a separate manual tagging step.

## Protected API

All Strategy DNA endpoints require the private admin/test bearer token.

- `GET /strategy-dna`
  - list strategy profiles and current versions
- `GET /strategy-dna/strategy/:id`
  - profile + versions + recent observations
- `POST /strategy-dna/profile`
  - create/update a profile
- `POST /strategy-dna/version`
  - create an immutable version snapshot and optionally mark it current
- `POST /strategy-dna/observation`
  - attach a research/forward observation to a version

The public GitHub Pages site never receives the admin token.

## Member layer later

Member strategy ownership should reuse the existing Discord-linked member identity/session rather than expose this admin API in the browser. The future Strategy Lab can then create owner-scoped profiles/versions while keeping Mason/system research separate.

## Why this matters

Signal Bridge is not just storing trades. The intended chain is:

`strategy version -> indicator version -> session behavior -> signal/pass -> journal evidence -> review -> next version`

Strategy DNA is the database spine that lets that chain remain queryable months later instead of being reconstructed from screenshots and memory.
