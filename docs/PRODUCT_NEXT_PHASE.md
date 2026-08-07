# Signal Bridge Product Next Phase

## Immediate beta polish
- Make interactive surfaces visually obvious on mobile and desktop.
- Remove duplicate homepage feature cards.
- Make Premium cards link to the product area they describe.
- Keep private journal capture private by default.
- Add an explicit admin-controlled publish path from Discord to the public Journal.
- Render published journal screenshots on the website.

## Next platform layer
- Discord OAuth / member identity.
- User-owned private journal inbox and screenshot review.
- Strategy Lab records owned by the member.
- Indicator presets / versions owned by the member.
- Signal entitlements and premium Discord roles.
- Durable screenshot storage outside Discord CDN.

## Bot completion before strategy research resumes
- `/status`: worker, journal, signal, and data-provider health.
- `/orb`: current ORB/session state from durable strategy events.
- `/brief`: premarket market-state summary.
- `/news`: actual economic calendar / red-news events, not generic headlines.
- Post-session lifecycle: ORB outcome, levels reached, setup/pass result.

## Monday end-to-end proof
Premarket note + screenshot → ORB/session events → trade or pass → Discord journal → selected publish → website review → post-session outcome.

The website is the system of record around the trading process; Discord is the fast interaction layer; Pine/strategy code is the market-state producer.
