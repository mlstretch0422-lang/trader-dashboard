# Signal Bridge Premium Access v1

Status: BACKEND / MEMBER UI IMPLEMENTED · DEPLOY + MIGRATION REQUIRED

## Product split

The GitHub Pages website remains the public preview, education, flagship strategy, and discovery surface.

The Cloudflare Worker owns the private member product at:

`/member`

This keeps private journal data, member-owned Strategy DNA, and entitlement checks off the public static site.

## Discord-linked sign-in

Use `/member-login` in the configured Signal Bridge Discord.

The command:

1. verifies the Discord interaction signature and guild;
2. resolves the user's current beta/premium entitlement;
3. creates a one-time login token;
4. returns an ephemeral link;
5. exchanges that link for a 24-hour HttpOnly/Secure/SameSite member session cookie.

`/journal-login` remains as a legacy alias during beta.

## Entitlement modes

### Friends / family beta

When `DISCORD_PREMIUM_ROLE_ID` is not configured, members of the configured Discord guild who use `/member-login` receive `BETA` access.

Discord users with Administrator or Manage Server receive `ADMIN` access.

### Paid / gated mode

When `DISCORD_PREMIUM_ROLE_ID` is configured, non-manager users must hold that exact Discord role when they use `/member-login`.

Successful role sync grants `PREMIUM` access in `member_entitlements`.

This means the launch gate can move from friends/family beta to a role-based paid community without rebuilding authentication.

## Locked member workspace

`/member` now provides a protected home with:

- My Journal
- Morning Desk shortcut
- Strategy Lab
- Indicator Workspace shortcut

### My Journal

Only rows whose `discord_author_id` matches the authenticated member are returned.

Private records remain private. Managers can explicitly publish/unpublish their own beta records from the protected workspace.

### Strategy Lab

The protected Strategy Lab uses Strategy DNA directly.

Members can:

- create a member-owned strategy identity;
- preserve version snapshots;
- assign the evidence stage for that version;
- record what changed;
- view system/flagship strategies read-only alongside their own.

Future indicator settings, session observations, signals, and journal links can attach to those same version IDs rather than creating a second strategy data model.

## Security boundary

- Public GitHub Pages receives no member session or admin token.
- Member cookies are HttpOnly, Secure, SameSite=Lax, scoped to `/member`.
- Strategy creation APIs require an authenticated member session and force owner identity server-side.
- A member cannot create a version under another member's strategy.
- Role gating is checked during Discord login, not trusted from browser input.

## Migration

`0009_member_entitlements.sql`

creates the durable entitlement ledger. It is designed to be applied after Strategy DNA migration 0008.
