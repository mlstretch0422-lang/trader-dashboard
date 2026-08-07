## Prioritized Components — Initial Draft

Generated: 2026-06-30

Ranked by current evidence + testability (higher = more evidence / higher priority to keep/test)

1. ORB Build & Midpoint (High priority)
   - Reason: Core structural anchor. Must be correct and reproducible.
   - Testability: Requires OHLC; implement canonical ORB builder and validate.

2. Stop / TP structure (High priority)
   - Reason: Reconstructed exits show Stop-dominated losses; TP exits are profitable on average.
   - Testability: Can analyze reconstructed trades now; can simulate on OHLC later.

3. One-trade-per-day enforcement (Medium-High)
   - Reason: System claims single trade/day; reconstructed trades show multi-trade days.
   - Action: Decide whether enforcement should be strict; test impact on PF and drawdown.

4. Retest requirement (Medium)
   - Reason: Project baseline claims midpoint retest is edge — current reconstructed data contradicts this.
   - Action: Re-tag trades using OHLC and re-evaluate performance of retest vs break.

5. VWAP filter (Medium)
   - Reason: Enabled by default in Pine; external docs suggest benefit.
   - Action: Test alignment filter vs baseline once OHLC is available.

6. EMA filter (Low-Medium)
   - Reason: Optional confirmation; lower priority than VWAP.

7. Body/ATR displacement filters (Low)
   - Reason: Fine-grained; useful to prevent whipsaw but may remove valid trades.

8. Adaptive sizing / pyramiding (Low)
   - Reason: Likely to introduce complexity and overfitting; treat as negative hypothesis.

9. HTF bias, liquidity sweeps, FVG, news filters, psychology modules (Research items)
   - Reason: Important for robustness but require manual annotations and additional data.

Next steps
- Reconcile labels via OHLC re-tagging (highest priority for correctness).
- Run focused tests for Stop/TP and one-trade-per-day effects using reconstructed trades now.
- After OHLC is provided, run full component sweeps and produce formal V1.0 spec + Pine code.
