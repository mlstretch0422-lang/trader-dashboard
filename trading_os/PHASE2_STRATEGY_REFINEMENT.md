# Phase 2: Strategy Refinement & Evidence-Based Iteration

**Status**: Framework Created (Awaiting Chart Screenshots)  
**Date**: July 1, 2026  
**Goal**: Build V2 that models your actual trading process, then validate/optimize objectively

---

## 🎯 Core Insight

V1 was mechanically correct but entered too early (premarket breakout). Your actual process is:

1. **Calculate ORB** (08:00-08:15 ET) as structure reference
2. **Wait for market open** (09:30 ET) for real liquidity
3. **Trigger on breakout + retest** or price action (FVGs, MSS, liquidity sweeps) off key levels
4. **Confirm with quantitative filters** (VWAP, EMA, volume, confluence)
5. **Respect price context** (read the market, don't blindly follow rules)

This is **discretionary trading framework with quantitative validation**, not pure mechanical.

---

## 📋 Your Actual Entry Process

### Entry Window: 09:30+ ET (Not 08:15)

```
08:00-08:15 ET: ORB Calculation (observation only)
08:15-09:30 ET: Premarket wait (no entries)
09:30+ ET: *** ENTRY WINDOW BEGINS ***
  - Look for: Breakout + Retest
  - Look for: Liquidity sweep/PA trade (if ORB invalid)
  - Confirm with: VWAP, EMA, volume, confluence
```

### Breakout + Retest Scenario

```
Condition 1: Price breaks above ORB_HIGH
  AND price has not broken below ORB_LOW
  
Condition 2: Price retraces back INTO the ORB range
  (creates opportunity for retest of ORB_HIGH)
  
Condition 3: Quantitative confirmation:
  - Price > VWAP (long filter)
  - EMA slopes up or aligned
  - Volume > average or displacement candle
  - Statistical confluence (3+ levels)
  
Condition 4: Price action confirmation:
  - FVG created on breakout? (structure)
  - MSS up? (structure confirmed)
  - Rejection candle on retest attempt? (strength)
  - Displacement candle on breakout? (momentum)
  
Entry: On retest candle close above ORB_HIGH
Stop: Below retest candle low or ORB_LOW (tighter)
Target: Previous resistance or 2R risk
```

### Liquidity Sweep / Price Action Scenario

```
Condition 1: ORB invalid (range too tight or choppy)
  OR price action setup off different structure
  
Key Levels (not just ORB):
  - Previous day high/low
  - London session high/low
  - Overnight session range
  - Volume hotspots
  
Condition 2: Liquidity sweep setup:
  - Price sweeps below key support (takes stops)
  - Rejection candle forms
  - MSS confirmed lower
  - FVG created on sweep
  
Condition 3: Quantitative confirmation:
  - Price positioning relative to VWAP
  - EMA alignment for direction
  - Volume increase on sweep
  
Entry: On reversal candle from sweep
Stop: Above sweep high
Target: Previous structure level
```

---

## 🔍 Price Action Hierarchy (Your Priority)

| Rank | Concept | Why | Application |
|------|---------|-----|-------------|
| 1 | **FVGs** | Identify imbalance, predict retest target | Set targets, identify weak breakouts |
| 2 | **MSS** | Confirm structure change | Primary signal for direction |
| 3 | **Liquidity Sweeps** | Find reversal points | Entry trigger on sweep rejection |
| 4 | **Rejection Candles** | Confirm rejection of level | Entry confirmation on retest |
| 5 | **Displacement Candles** | Show momentum | Confirm breakout strength |
| 6 | **Retest Behavior** | Understand price return | Fine-tune exit/scale points |

---

## 📊 Quantitative Filters (Your Priority)

| Rank | Filter | Why | Application |
|------|--------|-----|-------------|
| 1 | **VWAP** | Directional bias | Only trade above VWAP (long) |
| 2 | **EMA** | Trend confirmation | Entry only if EMA aligned |
| 3 | **Volume** | Entry quality | Confirm breakout/retest with volume |
| 4 | **Previous Day Levels** | Structure reference | Key areas for sweep/retest |
| 5 | **Confluence** | Statistical edge | Entry stronger with 3+ levels |

---

## 🖼️ Your Chart Layout (CRITICAL)

**We need to see your actual chart to design the indicator correctly.**

Typically includes:
- [ ] ORB high/low (marked as zone or line)
- [ ] Previous day high/low (reference levels)
- [ ] Overnight range (premarket box)
- [ ] London session range (if tracked)
- [ ] VWAP (and MA bands?)
- [ ] EMA setup (which EMA periods?)
- [ ] Volume profile or histogram
- [ ] Session boxes or time markers
- [ ] Key labels and color coding
- [ ] Dashboard helper (current stats?)

**Action**: Please share screenshots of your chart setup showing:
1. How you mark ORB levels
2. How you visualize overnight/London ranges
3. EMA setup and spacing
4. VWAP placement
5. Any custom indicators or labels
6. Overall color scheme and organization

---

## 📚 Research Phase (Outside Resources)

### To Research & Integrate

1. **ICT Concepts** (if applicable)
   - Fair Value Gaps formalization
   - MSS definition and detection
   - Liquidity concepts
   - Entry methodology

2. **Auction Market Theory**
   - Fair value concepts
   - Price acceptance vs rejection
   - Range establishment process

3. **Volume Profile & Order Flow**
   - Volume nodes and imbalance
   - Order flow patterns
   - Point of Control

4. **ORB Research & Statistics**
   - Academic studies on ORB effectiveness
   - Time-of-day bias
   - How ORB performs across markets
   - Retest vs breakout statistics

5. **Opening Range Strategies**
   - Professional ORB approaches
   - Entry timing variations
   - Exit methodologies
   - Risk/reward frameworks

6. **Bookmap-style Liquidity**
   - Understanding sweep behavior
   - Liquidity clustering
   - Large order detection

7. **Candle Pattern Research**
   - Displacement candle statistics
   - Rejection candle effectiveness
   - Inside bar behavior
   - Pin bar reversal patterns

---

## 🔄 Phase 2 Workflow (Iterative)

### Sprint 1: Model Your Process
1. [ ] Collect chart screenshots (you submit)
2. [ ] Document entry checklist (rules for breakout+retest scenario)
3. [ ] Document entry checklist (rules for liquidity sweep scenario)
4. [ ] Design new indicator matching your workflow
5. [ ] Create V2 strategy specification

### Sprint 2: Backtest & Compare
1. [ ] Backtest V2 on 6-month data
2. [ ] Compare V2 vs V1 metrics
3. [ ] Analyze screenshot examples
4. [ ] Identify what V2 caught that V1 missed

### Sprint 3: Research Integration
1. [ ] Gather external research
2. [ ] Propose improvements based on research
3. [ ] Test proposed changes
4. [ ] Document evidence for each change

### Sprint 4: Validation & Refinement
1. [ ] Paper trade V2 (50+ trades)
2. [ ] Collect your trade screenshots
3. [ ] Analyze actual entries vs rules
4. [ ] Refine rules based on live trading

### Repeat: Evidence-Based Iteration
- Every rule change needs measurable evidence
- Every research finding tested before implementation
- Every paper trade documented and analyzed
- Every quarter: evaluate, refine, optimize

---

## 📝 V2 Specification Framework (Draft)

### Entry Conditions (Version 2)

```yaml
ENTRY_WINDOW: 09:30 - 11:30 ET
MARKET_CONDITIONS: Breakout + Retest OR Liquidity Sweep

SCENARIO_A: "Breakout and Retest" (if ORB valid)
  Prerequisites:
    - ORB range > 10 pts, < 30 pts (valid range)
    - No extreme gaps or volatility
    - Pre-market volume reasonable
    
  Triggers:
    - Price breaks above ORB_HIGH + closes above
    - Price retraces into ORB range (creates retest)
    - Quantitative confirmation (VWAP, EMA, volume, confluence)
    - Price action confirmation (FVG, MSS, rejection, displacement)
    
  Entry: Close above retest high, above ORB_HIGH
  Risk: Below retest low or ORB_LOW (whichever tighter)
  Target: FVG target or previous resistance (structure-based)

SCENARIO_B: "Liquidity Sweep" (if ORB invalid or alternative)
  Key Levels: Previous day HML, Overnight range, Volume nodes
  
  Triggers:
    - Price sweeps below key support
    - Rejection candle forms at sweep low
    - MSS confirmed (higher high after sweep)
    - Price action confirmation (FVG, volume reversal)
    
  Entry: On reversal candle from sweep
  Risk: Above sweep high
  Target: Sweep high level or previous resistance
  
TIME_FILTERS: No entries after 10:30 ET (too late for full move)
SINGLE_POSITION: One active trade at a time
FORCED_FLAT: 11:00 ET (no overnight)
```

### Exit Conditions (Version 2)

```yaml
SCALE_OUT: If target clear
  - 25% at 1R (move risk distance)
  - 25% at 2R
  - 25% at 3R
  - 25% trail stop or structure

STOP_LOSS: 
  - Entry-based SL (below entry candle or ORB edge)
  - Structure-based SL (below sweep high or support)
  - Risk per trade: $100-200 (1-2 MES points on 1 contract)

FORCED_EXIT: 
  - 11:00 ET hard stop
  - Daily loss limit: $500 (stop trading)
```

---

## 🎯 Questions for Refinement

Once we see your charts, we'll refine:

1. **ORB Definition**: Valid range? How do you mark it?
2. **Retest Definition**: What counts as a valid retest? When is it "too late"?
3. **FVG Application**: Which FVGs matter (opening FVG only? All gaps?)
4. **MSS Definition**: How many highs/lows to confirm structure shift?
5. **Liquidity Sweep**: How low must price go to count as a sweep?
6. **Confluence Definition**: Which 3 levels create strongest setup?
7. **Volume Confirmation**: What volume level triggers entry?
8. **EMA Setup**: Which periods? How aligned do they need to be?
9. **VWAP Filter**: Is it hard (must be above) or soft (prefer above)?
10. **Time Filter**: Earliest entry 9:30? Latest entry 10:30?

---

## 📊 Expected V2 Improvements

**Compared to V1:**

| Aspect | V1 | V2 | Expected Improvement |
|--------|----|----|----------------------|
| **Entry Timing** | 8:15 (premarket) | 9:30+ (real liquidity) | Higher PF (better entries) |
| **Entry Type** | Breakout only | Breakout + retest + sweep | More scenarios (higher frequency) |
| **PA Signals** | None | FVG/MSS/rejection/displacement | Better quality trades |
| **Drawdown** | 29.6% | Lower (better entries) | Smoother equity curve |
| **Win Rate** | 31.6% | Higher (better retests) | Better psychology |
| **Expectancy** | $62.66 | Higher | Better R:R per trade |

**Primary hypothesis**: Entering on retest + price action confirmation > entering on raw breakout.

---

## 🚀 Next Steps

### Immediate (Next 24 hours)
1. [ ] Share your chart screenshots (current layout)
2. [ ] Provide trading notes/examples
3. [ ] Clarify any ambiguities in your process

### Short-term (This week)
1. [ ] Refine V2 specification based on your charts
2. [ ] Design new indicator matching your workflow
3. [ ] Gather initial research on FVGs, MSS, liquidity
4. [ ] Create V2 strategy code

### Medium-term (This month)
1. [ ] Backtest V2 on full 6-month data
2. [ ] Compare V2 vs V1 detailed results
3. [ ] Integrate research findings
4. [ ] Paper trade V2 (validate against live market)

### Long-term (Ongoing)
1. [ ] Every trade documented + analyzed
2. [ ] Every research finding tested
3. [ ] Every quarter: compare performance, refine rules
4. [ ] Build evidence base for your edge

---

## 🎓 Philosophy Shift

**V1 Approach**: "What does the backtest tell us?"  
**V2 Approach**: "What does your actual trading show? How do we model it? What does the market tell us?"

**V1 Question**: "How do we maximize profit?"  
**V2 Question**: "What is your actual edge? How do we validate it?"

**V1 Success**: System that made money on paper  
**V2 Success**: System that models your real process AND makes money with evidence

---

## 📌 Remember

This is not failure. This is exactly why we built V1.

Version 1 showed us what a fully mechanical system can do (not great). Now we build Version 2 based on your actual edge: **hybrid discretionary/quantitative, waiting for confluence, respecting market context**.

The market will teach us whether this edge is real.

Our job is to listen carefully, document everything, and build evidence.

---

**Status**: Ready for your chart screenshots.  
**Next Action**: Share your current trading chart setup (screenshots).  
**Timeline**: V2 specification complete within 48 hours of screenshots.  
**Goal**: Build a system that represents how you ACTUALLY trade, then prove it works.
