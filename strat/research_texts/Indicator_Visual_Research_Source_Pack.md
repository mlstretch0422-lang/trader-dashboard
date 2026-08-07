# Source: Indicator_Visual_Research_Source_Pack.docx

Indicator Visual Research Source Pack

Internal source review + external Pine/TradingView research for fixing the look of the RP overlay

Built for the Trading Strategy Mechanical project. Use this as the visual reference brief before the next rewrite.

Quick verdict

• The user’s live trade chart is cleaner because price still leads, while the current rebuild lets boxes, text, and helper objects compete too hard with price.

• The next rewrite should borrow the visual behavior of the reference indicators more directly instead of approximating them.

• The OR layer should look like the ORB overlay reference, the session layer should look like the killzone reference, the context lines should match the EMA/VWAP references, and the panel should remain the only custom layer that is visually distinct.

• The project should keep historical ORs and session context visible by default, because the build spec says review and backtesting require preserved structure.

Visual comparison

Reference trade chart vs. current failed rebuild. The gap is mainly in visual hierarchy, object density, and the way the reference indicators control opacity, labels, and history.

Reference trade chart: clean session stack, preserved structure, lighter labels, OR levels that read like chart tools.

Current rebuild problem: too much dark fill, weak OR emphasis, helper objects competing with price, panel fine but chart body off.

What the internal sources already prove

• The build spec already says the target is a professional execution-support indicator that visually matches the ES/NQ workspace, keeps historical ORs visible, keeps session structure obvious, and uses sparse fixed markers rather than cluttered debug objects.

• The RP research dossier already locks the core clock to 8:00-8:15 New York and treats the ORB as one module inside a bigger decision framework, not the whole setup.

• The Pine checklist already says to use boxes, lines, labels, and tables for the right jobs, keep dynamic text out of plotshape, and reset persistent state intentionally.

• So the real missing piece is not more strategy logic. It is a better visual blueprint and a more faithful merge of the four reference overlays.

Reference indicators: what to borrow from each one

What external research adds

• TradingView’s Pine docs explicitly say lines and boxes are better than plots when you need support/resistance, price ranges, and custom formations at arbitrary chart positions. They also recommend arrays when managing active drawings.

• TradingView’s text-and-shapes docs say labels are objects designed for dynamic text and flexible placement, while plotshape and plotchar are better for fixed symbols and const text only.

• TradingView’s Lux ORB page frames the OR as a rigid, customizable range used to distinguish ranging versus trending days, with mean/ORM and side-of-range logic central to management.

• TradingView’s TFO killzones page explicitly emphasizes five fully customizable sessions, pivots that extend until invalidated, a cutoff time to keep the chart clean, and drawing limits to reduce clutter.

• TradingView’s blog on force_overlay is useful later if the project ever wants the big table off the main chart, but it is not the main fix right now.

Visual best-practice rules that come directly out of those references

• Use box.new + line.new + xloc.bar_time for the OR and session structures, not a mix of unrelated plots pretending to be ranges.

• Use arrays to retain only the most recent N historical ORs, session boxes, pivot lines, and labels.

• Keep labels optional and tiered: session name labels can be on by default, pivot labels should default off or to a reduced subset.

• Default opacity should be light enough that price remains the star. The references use transparency as a cleanliness control, not a side effect.

• Use settings that mirror the source indicators: custom session times, text toggles, label size, line style, extension rules, and drawing limits.

Why the current rebuild keeps missing the look

• The OR layer has been treated like a custom debug layer instead of being rebuilt around the ORB reference’s native visual behavior.

• The session layer has been rebuilt as a rough approximation instead of inheriting the TFO layout logic: session box limits, text controls, pivot extension rules, and clutter controls.

• Too many defaults are visually loud. Your live chart uses many objects, but most of them are low-opacity, lower priority, or selectively labeled.

• The rebuild keeps mixing a custom panel with a custom chart language. The panel can stay custom. The chart language should mostly copy the reference overlays.

Exact visual blueprint for the next rewrite

Recommended build order

1. Rebuild the chart body first: Lux-style OR layer + TFO-style killzone layer + exact EMA/VWAP context.

2. Only after the visual stack matches the trade chart should the RP confirmation markers be re-laid on top.

3. Keep the panel last, because it is already the least broken part.

4. Do not revisit strategy conversion until the overlay actually looks and reads like the user’s trade screen.

Next-action brief for the next code pass

Source appendix used for this pack