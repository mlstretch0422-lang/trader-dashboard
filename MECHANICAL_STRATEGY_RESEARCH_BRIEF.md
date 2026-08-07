# Mechanical Strategy Research Brief

## Purpose

This document gives the strategy bot / VS Code AI assistant a research backbone for building, testing, and improving a mechanical trading strategy.

The goal is not to find a magic indicator.

The goal is to turn the strategy into a clean, testable decision engine:

```text
bias → setup → trigger → risk → execution → validation
```

This should be used as design guidance for building indicators, strategies, optimizer toggles, and funded-mode backtests.

---

## Core Philosophy

A real mechanical strategy should behave like a rule-based machine, not a prediction machine.

The bot should avoid vague logic like:

```text
price looks bullish
momentum seems strong
good-looking setup
```

Instead, it should use locked, testable conditions like:

```text
close > HTF midpoint
price swept ORB low
price reclaimed ORB low
VWAP alignment is bullish
trade time is before 10:30
daily loss limit has not been hit
```

Every trade should answer:

1. What is the bias?
2. What level matters?
3. What setup occurred?
4. What trigger confirmed it?
5. Where is the stop?
6. Where is the target?
7. Is the trade allowed under funded-mode risk rules?
8. Does the system survive trailing drawdown?

---

# 1. Historical Mechanical Strategy Models

## 1.1 Turtle Trading

The Turtle Traders experiment is one of the best examples of a complete mechanical trading system.

Richard Dennis and William Eckhardt trained beginners to follow a strict rules-based trend-following system. The key lesson is not that the Turtle system itself should be copied. The key lesson is that a strategy can be fully broken into rules:

- Markets traded
- Entry rules
- Exit rules
- Stop placement
- Position sizing
- Volatility adjustment
- Risk limits
- Discipline rules

Use the Turtle model as an example of mechanical completeness.

Do not use it as a direct trading system unless specifically testing trend-following baselines.

### What to extract from Turtle Trading

```text
A system is not just an entry signal.
A system includes:
- when to trade
- what to trade
- how much to trade
- when to stop
- when to exit
- when to do nothing
```

---

## 1.2 Dow Theory / Trend-Following Structure

Dow Theory and early trend-following systems are useful because they convert market behavior into objective states.

Instead of saying:

```text
I think the market is bullish
```

A mechanical system should define trend through structure:

```text
higher highs and higher lows
price above major midpoint
price holding above VWAP
higher timeframe direction aligned
```

This matters because the bot should code bias as a state, not as a feeling.

Example:

```python
if close > htf_midpoint and close > vwap and ema_fast > ema_slow:
    bias = "BULLISH_ALLOWED"
elif close < htf_midpoint and close < vwap and ema_fast < ema_slow:
    bias = "BEARISH_ALLOWED"
else:
    bias = "NEUTRAL_NO_TRADE"
```

---

## 1.3 Opening Range / ACD-Style Logic

Opening range systems are historically important because they use the first part of the session to define key levels.

This supports the idea of coding:

```text
opening_range_high
opening_range_low
orb_midpoint
breakout_level
failed_breakout
retest_level
session_bias
time_cutoff
```

For this strategy, the opening range should not be treated as a blind breakout signal.

The better version is:

```text
Opening range level → liquidity sweep → reclaim/rejection → confirmation → risk check
```

Not:

```text
ORB breaks → instantly enter
```

---

# 2. Known Dangers in Mechanical Strategy Development

## 2.1 False Breakouts

Raw breakout systems often look good in backtests but fail live because of false breaks, sweeps, and poor fills.

The bot should assume that simple range breakouts are dangerous unless confirmed.

Required confirmation ideas:

- Liquidity sweep
- Reclaim of swept level
- Rejection wick
- Strong close back inside/outside level
- VWAP alignment
- EMA alignment
- Higher timeframe bias
- Time-of-day filter
- Volume confirmation
- No red news nearby

The strategy should reward quality of confirmation, not just more trades.

---

## 2.2 Overfitting

Overfitting happens when the bot keeps adjusting parameters until the past looks perfect, but the system fails on new data.

Warning signs:

- Too many toggles
- Too many optimized values
- Tiny changes destroy performance
- One month carries the entire backtest
- Great net profit but ugly drawdown
- Passes one sample but fails other periods
- Strategy only works on one exact stop/target combo

The bot should reject candidates that are profitable only because of curve-fit behavior.

---

## 2.3 Lookahead Bias

Lookahead bias happens when the backtest uses information that would not have been available at the time of the trade.

Examples:

```text
Using the final candle close before the candle actually closes
Using the full day high/low during the morning
Using future VWAP values
Using a completed 5m candle while trading inside that candle
Using final session data to decide an earlier trade
```

The execution simulator must process bars in chronological order.

No trade decision can use future information.

---

## 2.4 Bad Fill Assumptions

A backtest can lie if it assumes perfect fills.

The strategy should include:

- Slippage
- Commission
- Spread assumptions
- Stop-market fill realism
- Entry on next candle where appropriate
- Conservative limit-fill modeling

For funded-mode testing, assume worse fills rather than perfect fills.

---

## 2.5 Trailing Drawdown Death Spiral

Trailing drawdown is one of the main account killers in funded evaluations.

A system can have positive expected value but still fail a trailing drawdown model because of:

- Early losses
- Large unrealized retracements
- Too much size too soon
- Low pass cadence
- Win/loss clustering
- Giving back open profit
- Daily losses stacking during chop

Therefore, the bot should rank strategies by survival first, not total profit first.

---

# 3. Mechanical System Architecture

The strategy should be separated into clean modules.

Recommended modules:

```text
bias_engine.py
session_levels.py
entry_triggers.py
risk_engine.py
execution_simulator.py
optimizer.py
walk_forward.py
report_generator.py
```

---

## 3.1 Bias Engine

The bias engine determines whether long trades, short trades, both, or neither are allowed.

Possible states:

```text
BULLISH_ALLOWED
BEARISH_ALLOWED
NEUTRAL_NO_TRADE
CONFLICT_NO_TRADE
NEWS_BLOCKED
TIME_BLOCKED
DAILY_STOP_BLOCKED
```

Example bias logic:

```python
def get_bias(close, htf_midpoint, vwap, ema_fast, ema_slow):
    if close > htf_midpoint and close > vwap and ema_fast > ema_slow:
        return "BULLISH_ALLOWED"

    if close < htf_midpoint and close < vwap and ema_fast < ema_slow:
        return "BEARISH_ALLOWED"

    return "NEUTRAL_NO_TRADE"
```

Bias should not trigger trades by itself.

Bias only decides what direction is allowed.

---

## 3.2 Session Levels

Session levels define the battlefield.

Important levels:

```text
Asia high
Asia low
London high
London low
ORB high
ORB low
ORB midpoint
Previous day high
Previous day low
Previous day close
Premarket high
Premarket low
VWAP
HTF midpoint
```

The bot should compute these levels before looking for entries.

---

## 3.3 Setup Logic

A setup is the market condition that prepares a possible trade.

Examples:

```text
price swept ORB low
price swept ORB high
price swept London low
price swept London high
price tapped HTF midpoint
price entered FVG
price returned to VWAP
```

A setup does not equal an entry.

A setup only arms the strategy.

Example:

```python
if price_swept_orb_low and bias == "BULLISH_ALLOWED":
    long_setup_armed = True
```

---

## 3.4 Trigger Logic

A trigger confirms that the setup is tradable.

Examples:

```text
reclaim close
rejection wick
engulfing candle
strong body candle
close back above ORB low
close back below ORB high
VWAP reclaim
EMA reclaim
```

Example:

```python
if long_setup_armed and close > orb_low and rejection_wick:
    enter_long = True
```

The trigger should be stricter than the setup.

---

## 3.5 Risk Engine

The risk engine controls whether a trade is allowed and how large it can be.

Rules to include:

```text
max trades per day
daily loss limit
overall drawdown limit
trailing drawdown model
stop size limit
target size
R multiple
max position size
contract scaling rule
time cutoff
news block
```

The risk engine should be able to say:

```text
TRADE_ALLOWED
TRADE_BLOCKED_DAILY_LOSS
TRADE_BLOCKED_TIME
TRADE_BLOCKED_NEWS
TRADE_BLOCKED_MAX_TRADES
TRADE_BLOCKED_DRAWDOWN
```

---

## 3.6 Execution Simulator

The execution simulator should model how trades would actually happen.

It should include:

- Entry price
- Stop price
- Target price
- Slippage
- Commission
- Bar-by-bar order resolution
- Whether stop or target hit first
- Force-flat logic
- Breakeven logic if enabled
- Partial exits if enabled

It must avoid lookahead bias.

---

## 3.7 Optimizer

The optimizer should test strategy toggles, not vague ideas.

Example toggles:

```text
use_htf_midpoint_filter
use_vwap_alignment
use_ema_alignment
use_liquidity_sweep
use_orb_retest
use_london_level
use_reclaim_close
use_rejection_wick
use_engulfing_trigger
use_volume_filter
use_news_filter
use_breakeven
use_trailing_stop
```

The optimizer should not optimize everything at once without discipline.

Start with core survival rules locked, then test small controlled variations.

---

## 3.8 Walk-Forward Validation

The bot should not optimize on one big historical period and call it done.

Use chronological validation:

```text
Train / optimize period
Walk-forward validation period
Final out-of-sample holdout
```

Example:

```text
2022 → optimize
2023 → validate
2024 → optimize
2025 → validate
2026 → final holdout
```

Rank by out-of-sample survival, not just in-sample profit.

---

# 4. Funded-Mode Profile

The strategy should be tested like a funded evaluation, not like a fantasy backtest.

## 4.1 Account Profile

Use Alpha Futures-style 50k assumptions unless otherwise specified.

```text
Account size: $50,000
Profit target: $3,000
Daily loss limit: $2,000 firm max
Strategy daily loss target: around $200
Monthly target: $3,000–$5,000, but not forced
Primary product: MES
ES math may be used for scaling projections
```

---

## 4.2 Drawdown Modeling

Test both:

```text
static drawdown
trailing drawdown
```

But rank trailing drawdown survival higher.

Trailing drawdown is the main killer.

---

## 4.3 Trade Frequency

Primary model:

```text
max trades per day: 1
trade window: 9:30–10:30 for new entries
force flat: 11:00 if needed
```

Secondary model only:

```text
allow 2nd trade only after first trade loses
only if daily loss cap is not violated
only if full confluence is present
no revenge logic
hard daily stop required
```

Do not make 2 trades/day the default unless testing specifically proves it survives better.

---

# 5. Current Strategy Direction

The current preferred model is not a broad ORB breakout model.

The preferred model is:

```text
liquidity sweep → reclaim/rejection → confirmation → funded-mode risk check
```

Hard-lock these for strict survival batches:

```text
use_liquidity_sweep = true
use_bull_rejection = true
no_new_trades_after = 10:30
```

Use ORB levels as context, not automatic breakout entries.

---

# 6. Optimizer Toggle Map

## 6.1 Bias Toggles

```text
htf_midpoint_required
vwap_alignment_required
ema_alignment_required
previous_day_direction_filter
trend_structure_required
```

## 6.2 Setup Toggles

```text
liquidity_sweep_required
orb_retest_required
london_level_required
fvg_required
premarket_level_required
previous_day_level_required
```

## 6.3 Trigger Toggles

```text
reclaim_close_required
rejection_wick_required
engulfing_required
minimum_body_percent
minimum_close_strength
confirmation_candle_required
```

## 6.4 Risk Toggles

```text
fixed_stop_points
structure_stop_enabled
target_r_multiple
fixed_target_points
breakeven_trigger
max_daily_loss
max_trades_per_day
max_contracts
```

## 6.5 Time Toggles

```text
trade_start_time
no_new_trades_after
force_flat_time
avoid_news_minutes_before
avoid_news_minutes_after
```

## 6.6 Validation Toggles

```text
in_sample_score
out_of_sample_score
walk_forward_score
trailing_dd_survival_score
daily_loss_violation_count
worst_losing_sequence
```

---

# 7. Candidate Ranking Rules

Do not rank candidates by net profit alone.

Rank candidates by:

1. Trailing drawdown survival
2. Max drawdown
3. Worst losing sequence
4. Daily loss violation count
5. Consistency of daily PnL
6. Profit factor
7. Average R
8. Pass cadence
9. Total net profit

If a strategy passes faster but has ugly trailing drawdown behavior, reject it.

If a strategy has lower profit but survives better and is easier to trade, prefer it.

---

# 8. Required Reports

Each optimizer run should produce:

```text
top_candidates.csv
rejected_candidates.csv
trade_log.csv
daily_pnl.csv
equity_curve.csv
drawdown_curve.csv
walk_forward_results.csv
funded_mode_summary.md
```

The summary should explain:

```text
why the top candidates survived
why rejected candidates failed
whether results were in-sample or out-of-sample
whether trailing drawdown was violated
how many days hit daily stop
worst losing streak
best and worst months
realistic pass cadence
```

---

# 9. Bot Instructions

Use this as the main design instruction:

```text
Do not build a curve-fit monster.

Build a funded-mode survival engine.

The strategy should behave like a mechanical decision system:
bias → setup → trigger → risk → execution → validation.

Prioritize clean entries, drawdown control, and live-like behavior over maximum historical profit.
```

---

# 10. Practical Implementation Prompt

Use this prompt when asking the AI coding assistant to work on the strategy:

```text
Read MECHANICAL_STRATEGY_RESEARCH_BRIEF.md.

Refactor the strategy into a mechanical state-machine architecture.

Separate the system into:
- bias_engine.py
- session_levels.py
- entry_triggers.py
- risk_engine.py
- execution_simulator.py
- optimizer.py
- walk_forward.py
- report_generator.py

The current preferred strategy is not a broad ORB breakout.

The preferred strategy is:
liquidity sweep → reclaim/rejection → confirmation → funded-mode risk check.

Hard-lock:
- use_liquidity_sweep = true
- use_bull_rejection = true
- no_new_trades_after = 10:30

Primary model:
- max trades/day = 1
- new entries only from 9:30 to 10:30
- force flat by 11:00 if needed
- MES-first execution
- ES point-value math allowed for scaling and funded target modeling

Rank strategy candidates by:
1. trailing drawdown survival
2. max drawdown
3. worst losing sequence
4. daily loss violations
5. consistency
6. profit factor
7. pass cadence
8. total net profit

Do not optimize for maximum profit first.
Optimize for survival-first funded-mode behavior.
```

---

# 11. Final Rule

The system should not try to prove that the strategy is good.

The system should try to break the strategy.

If it still survives after realistic slippage, commissions, time filters, daily loss caps, trailing drawdown rules, and out-of-sample validation, then it is worth forward testing.
