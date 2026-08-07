# Source: Trading_Strategy_V1_Restart_Brief.docx

Trading Strategy V1 Restart Brief

Source document for restarting from the working V1 indicator and the first simple V1 strategy only.

Current objective

Rebuild one clean strategy from scratch that mirrors the V1 indicator’s behavior as closely as possible.

The immediate target is not optimization. The immediate target is a strategy that compiles, executes trades, and matches the intended V1 trigger path.

No new filters, no second trades, no adaptive sizing, no dashboard expansion, no extra sessions until the core V1 strategy is proven to trade.

Locked inputs and assumptions

Use the V1 indicator as the source of truth for ORB build, breakout, displacement, midpoint pullback, and reclaim trigger behavior.

Use the first simple working strategy as the source of truth for how orders are placed, managed, and closed in TradingView.

Treat all later rewrites and non-firing merge versions as invalid references unless the user explicitly asks to revisit them.

Hard bans for the next rebuild

Do not start from any merge, adaptive, or debug strategy file.

Do not add EMA, VWAP, ADX, ORB-half, SMT, liquidity extras, or environment filters.

Do not mix indicator visuals and strategy plumbing in the same first pass beyond the minimum needed to verify signals.

Do not patch prior broken code. Rewrite cleanly from zero.

Do not send code until the logic path has been compared directly to the V1 indicator and the order path has been compared directly to a working strategy example.

Required rebuild sequence

Step 1: Restate the exact V1 rules in plain English before coding.

Step 2: Copy only the session / ORB / breakout / displacement / pullback / trigger logic from the working V1 indicator.

Step 3: Copy only the order placement style from a known working strategy shell.

Step 4: Build the bare strategy first with fixed contracts, one entry model, simple stop, and simple target.

Step 5: Compile-check every syntax-risk area before sending.

Step 6: Only after the strategy executes trades should any filters or visual extras be considered.

Syntax and compile checklist

Verify Pine version consistency before writing any code.

Check assignment syntax, especially multiline boolean expressions.

Do not use unsupported strategy arguments for the Pine version in use.

Check strategy.entry and strategy.exit signatures against the official docs before sending.

Check table.clear argument count, ta.vwap usage, ta.dmi usage, and any series vs simple mismatches before sending.

Definition of success for V1 restart

The script compiles cleanly.

The script places trades.

The trades occur only when the V1 indicator’s trigger logic would justify them.

The code is simple enough to inspect line by line without hidden rule drift.

Definition of failure

Any new code that does not trade.

Any code that introduces extra filters not requested.

Any response that claims progress without proving that the strategy shell and V1 logic were matched on purpose.