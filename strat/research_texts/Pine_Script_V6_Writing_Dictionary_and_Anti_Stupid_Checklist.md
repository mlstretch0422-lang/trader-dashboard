# Source: Pine_Script_V6_Writing_Dictionary_and_Anti_Stupid_Checklist.docx

Pine Script® v6 Writing Dictionary
& Anti-Stupid Checklist

A project source document for building TradingView indicators cleanly,
compiling on the first pass more often, and avoiding circular debug hell.

Built for: Trading Strategy Mechanical project
Recommended use: keep this in Sources and treat it like a pinned preflight checklist.

1. Non-negotiable mindset rules

Indicators and strategies are different jobs. Build the indicator first. Build the strategy later.

Do not patch blindly. If the script is structurally messy, rewrite it clean.

Do not add filters just because they sound smart. Every filter must have a job.

Do not send code until you have done a syntax-risk pass and a logic pass.

If TradingView throws one compile error, fix that error first before touching logic.

2. Hard Pine rules that keep biting this project

These are the rules most likely to prevent your code from even getting onto the chart.

3. Pine type system — the part that causes half the fake logic bugs

Official docs emphasize that Pine uses types and type qualifiers to control where a value can be used. In practice, most painful errors come from mixing constant text, inputs, and bar-by-bar series values in the wrong places.

4. Visuals dictionary — what to use for what

5. Session, state, and reset rules

Use explicit session booleans: inOrbSession, inTradeWindow, inForceFlat.

Use a clean new-day reset for all var state that should not survive into the next day.

Breakout should stamp once. Pullback should only be allowed after breakout. Trigger should only be allowed after a valid pullback.

If you store bar indexes such as breakoutBarIdx or pullbackBarIdx, compare against them explicitly when you want sequence integrity.

When a state machine matters, write it as a sequence: ORB -> breakout -> displacement -> pullback -> trigger. Do not blur steps together.

6. Project-specific compile traps to check before sending code

7. Indicator-writing dictionary for this project

ORB variables: orbHigh, orbLow, orbMid, orbRange, midTop, midBot

State booleans: orbDone, breakoutLong, breakoutShort, displacementOK, pullbackSeen, pullbackValid, triggerLong, triggerShort

State indexes: breakoutBarIdx, pullbackBarIdx, triggerBarIdx

Confluence booleans: emaPass, vwapPass, orbHalf, goodEnv, badEnv, hardAllMet

Display objects: table for checklist, plot for ORB lines, plotshape for fixed bar markers, label.new for dynamic text

Reset anchors: newDay, session open, session end, force-flat window if used later

8. Preflight checklist before sending Pine code

Am I in the correct mode right now: indicator work, strategy work, research, or debugging?

Did I preserve the locked objective, or did I sneak in new filters and complexity?

Did I confirm Pine version compatibility?

Did I check plotshape text for const-string problems?

Did I check for type qualifier mismatches: const/input/simple/series?

Did I reset every persistent var that should reset?

Did I separate the sequence cleanly: ORB -> breakout -> displacement -> pullback -> trigger?

Did I avoid mixing indicator code with strategy expectations?

Did I verify table updates and clear behavior?

Would this code compile before I talk about how good the logic is?

9. Bare-minimum code patterns worth copying

A. Fixed marker text only

plotshape(cond, title = "PB Valid", style = shape.diamond, location = location.bottom, color = color.lime, size = size.small, text = "PB")

B. Dynamic text belongs in labels

label.new(bar_index, high, text = "Depth: " + str.tostring(depthPct))

C. Dashboard pattern

var table dash = table.new(position.top_right, 2, 10)
if barstate.islast
    table.clear(dash, 0, 0, 1, 9)
    table.cell(dash, 0, 0, "Direction")

D. Sequence guard on pullback

canSeekPullback = displacementOK and not na(breakoutBarIdx) and bar_index > breakoutBarIdx

10. Official references to keep in Sources

TradingView Pine Script® Language Reference Manual v6 - https://www.tradingview.com/pine-script-reference/v6/

TradingView Type system documentation - https://www.tradingview.com/pine-script-docs/language/type-system/

TradingView Visuals: text and shapes - https://www.tradingview.com/pine-script-docs/visuals/text-and-shapes/

TradingView Visuals overview - https://www.tradingview.com/pine-script-docs/visuals/overview/

TradingView FAQ: strings and formatting - https://www.tradingview.com/pine-script-docs/faq/strings-and-formatting/

TradingView Migration guide to Pine v6 - https://www.tradingview.com/pine-script-docs/migration-guides/to-pine-version-6/

TradingView Strategies FAQ / Concepts - https://www.tradingview.com/pine-script-docs/faq/strategies/

11. Project command rules

Do not restart from scratch unless explicitly asked.

Do not patch when a clean rewrite is needed.

Do not research without ending in build / remove / retest.

Do not add filters without a defined job.

Do not send Pine code without a syntax-risk pass.

Do not drift away from the real objective: a mechanical indicator that supports execution.