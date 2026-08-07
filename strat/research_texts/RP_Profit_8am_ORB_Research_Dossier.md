# Source: RP_Profit_8am_ORB_Research_Dossier.docx

RP Profit Method
Research Dossier

8:00–8:15 ORB model, surrounding confluences, non-ORB day behavior,
and implementation notes for the Trading Strategy Mechanical project

Built from public web research + your existing project docs
Date: 2026-04-07

1. What this document is for

This document is a working research sheet for your project, not a sales summary. The goal is to pin down the public structure around the RP-style 8:00–8:15 ORB method, the extra pieces that seem to sit around it, and what should be coded as separate modules versus what should remain discretionary.

2. Executive takeaways

The core public model is an 8:00–8:15 AM New York opening range, then a break / retest style execution around that range or its midpoint.

Multiple public snippets around RP / RP-adjacent content stress that the raw ORB alone is not enough; confirmation, higher-timeframe context, and liquidity framing matter.

A third-party programmatic backtest of the pure 8AM ORB reported poor long-run results, which strongly suggests the edge is in the filters and context rather than in the range itself.

Your indicator should therefore be modular: OR box, HTF levels, liquidity markers, session filters, and confirmation states should each work separately and also roll up into one decision panel.

For non-ORB days, the research points toward liquidity sweeps, equal highs/lows, higher-timeframe candle context, and “wait for confirmation” rather than forcing an ORB trade every session.

3. Publicly confirmed pieces of the method

3.1 The opening range window

Across public YouTube / Instagram snippets tied to RP or explicitly referencing RP, the repeated opening range is the first 15 minutes after 8:00 AM New York time, i.e., 8:00–8:15. Several third-party rebuild/backtest snippets also explicitly call it the “RP Profits 8:00–8:15 ORB” and describe the trade zone as the price range built between 8:00 and 8:15.

3.2 The execution style is not just “buy the break”

Public descriptions repeatedly frame the entry as a break-and-retest / midpoint retest rather than blind momentum chasing. The recurring language is “break and retest,” “retest zone,” and “midpoint retest.” That lines up with your own discretionary notes and is important because it means the opening range itself is just the first structure layer, not the final trigger.

3.3 Confirmation matters

Several public snippets around the RP ecosystem explicitly say the most common ORB mistake is entering too early and that “no confirmation = no trade.” That is consistent with using reclaim candles, body strength, sweeps, or alignment with other context rather than raw breakout alone.

3.4 Higher-timeframe candles are part of the worldview

Public snippets tied to the same content ecosystem repeatedly emphasize 4-hour and 1-hour candle closes, plus HTF overlays that let traders keep 15m / 30m / 1H / 4H candles on one execution chart. That does not prove a specific fixed rule, but it strongly confirms that HTF context is not optional background in this method family.

3.5 Equal highs / equal lows and liquidity magnets

Public posts around the RP account also emphasize equal highs / equal lows as magnets, “engineered relative equal highs,” and liquidity sweeps. This matters because it gives a plausible explanation for why some apparent “failed ORB days” may actually be liquidity-tap days that should be interpreted differently instead of filtered out blindly.

4. What the research says about the raw 8AM ORB by itself

One of the strongest public datapoints is a third-party backtest reel that explicitly asked whether the 8AM ORB works long-term when implemented programmatically and executed perfectly. The public snippet says the answer was “a resounding no,” and the follow-up snippet reports 415 trades, 16% winners, and a 0.87 profit factor over the tested sample. Whether or not that specific backtest is perfectly faithful, it is a major warning sign: the range alone is probably not the edge.

5. Working model of how the method is likely assembled

Below is the best synthesis of what appears to be happening when you combine the public evidence with your notes. Items marked “High confidence” are directly supported by public snippets. Items marked “Moderate” are consistent with the public material plus your repeated observations, but not all of them are cleanly documented as fixed RP rules.

6. What to look for on non-ORB days

This is the part you specifically asked for. I could not find a single public source that lays out a clean “non-ORB day playbook” from RP in one place. So this section is an evidence-based synthesis, not a quoted official rulebook.

If the opening range is oversized or ugly, treat the ORB as informational context only, not as a trade trigger.

Watch whether price is simply sweeping equal highs / equal lows or prior session highs/lows and then reclaiming. Public snippets heavily support liquidity magnets and sweeps as a core idea in this ecosystem.

On chop mornings, a one-sided breakout that immediately fails may still be useful if it clearly taps a liquidity pool and then reclaims back through the range or midpoint.

Higher-timeframe candle context (especially 1H / 4H) may decide whether the day is a trend continuation day, a reversal day, or a no-trade day.

Wait for confirmation. Public content around this method repeatedly warns against early entries and emphasizes not forcing the breakout.

This suggests your final toolset should include both: (a) ORB mode, and (b) liquidity/context mode that still functions when no clean ORB trade exists.

7. Indicator modules to build separately, then combine

Module A — ORB structure

8:00–8:15 New York range box

ORH / ORL / ORM extension lines

range-size readout

hard filter: no setup if OR range > user limit (for example 20 points on ES)

Module B — Higher-timeframe context

1H and 4H highs/lows or candle boundaries

optional recent midpoint / equilibrium references

bull / bear / neutral bias state

Module C — Liquidity map

Asia and London highs/lows

prior session highs/lows

equal highs / equal lows markers

optional sweep / reclaim status

Module D — Confirmation layer

breakout body quality

retest depth

reclaim candle

VWAP / EMA / structure alignment

Module E — Decision panel

separate yes/no rows for each module

never let the panel hide which module actually failed

keep “ORB valid” separate from “trade valid”

8. Filters worth testing first

Oversized OR filter: skip if 8:00–8:15 range > X points.

Minimum displacement after break before any retest can count.

One-sided liquidity confirmation: only take the setup if the break aligns with the day’s intended liquidity draw or if the opposite-side sweep has already completed.

No double-sided mess: skip if price breaks both sides of the OR before confirmation.

Optional HTF alignment: only allow longs above chosen HTF reference and shorts below it.

Optional environment filter: skip if midpoint gets crossed too many times before trigger.

9. What is still unverified

Exact official RP entry candle definition beyond the public “break and retest” language.

Exact stop placement hierarchy on ES vs NQ for every variation.

Exact non-ORB day rules from RP in one documented source.

Whether RP’s public examples are meant as a complete system or as a gateway framework that still depends on live chart reading.

10. What actually applies to your project right now

Lock the ORB clock to 8:00–8:15 New York time.

Keep the ORB drawing layer, but add a max-range filter.

Separate “ORB valid” from “setup valid” in the checklist panel.

Add higher-timeframe and liquidity modules as independent layers before trying to merge everything into one binary execute signal.

Treat non-ORB days as a separate research lane instead of trying to force every morning into the ORB bucket.

Appendix A — Public source notes used for this dossier

Important: because many of the public references available to me are search-result snippets from social/video platforms rather than full written rulesets, this dossier intentionally separates confirmed public signals from inferred project guidance.