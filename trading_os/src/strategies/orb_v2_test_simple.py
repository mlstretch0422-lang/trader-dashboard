#!/usr/bin/env python3
"""
ORB V2 Strategy - Ultra-simplified test backtest
Focus on getting ANY trades to generate first
"""

import pandas as pd
import numpy as np

print("\n" + "="*70)
print("ORB V2 TEST - ULTRA SIMPLE")
print("="*70)

# Load data
print("\n1. Loading data...")
df = pd.read_csv('ES_backtest_data.csv')
print(f"   ✓ Loaded {len(df):,} rows")

# Convert datetime
print("2. Converting datetime...")
df['datetime'] = pd.to_datetime(df['datetime'])
df['hour'] = df['datetime'].dt.hour
df['minute'] = df['datetime'].dt.minute
df['date'] = df['datetime'].dt.date
df['time_min'] = df['hour'] * 60 + df['minute']
print(f"   ✓ Time ranges: {df['time_min'].min()} to {df['time_min'].max()} minutes")

# Calculate basic indicators
print("3. Computing indicators...")
df['body'] = abs(df['close'] - df['open'])
df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()
df['avg_vol_20'] = df['volume'].rolling(20).mean()
df['avg_body_20'] = df['body'].rolling(20).mean()
df = df.fillna(method='ffill')
print(f"   ✓ Indicators computed")

# Compute VWAP per day
print("4. Computing VWAP...")
vwap_dict = {}
for date in df['date'].unique()[:100]:  # Test with first 100 days
    day_mask = df['date'] == date
    day_data = df[day_mask]
    tp = (day_data['high'] + day_data['low'] + day_data['close']) / 3
    pv = tp * day_data['volume']
    cum_pv = pv.cumsum()
    cum_v = day_data['volume'].cumsum()
    day_vwap = cum_pv / cum_v
    for idx, val in zip(day_data.index, day_vwap):
        vwap_dict[idx] = val

df['vwap'] = df.index.map(lambda x: vwap_dict.get(x, df.loc[x, 'close']))
print(f"   ✓ VWAP computed for test dates")

# Run backtest
print("5. Backtesting...")
trades = []
daily_orbs = {}

for i, (idx, row) in enumerate(df.iterrows()):
    if i % 100000 == 0:
        print(f"   Processing bar {i:,}...")
    
    date = row['date']
    time_min = row['time_min']
    
    # Collect ORB data (08:00-08:15 = 480-495 min)
    if 480 <= time_min <= 495:
        if date not in daily_orbs:
            day_mask = (df['date'] == date) & (df['time_min'] >= 480) & (df['time_min'] <= 495)
            orb_data = df[day_mask]
            if len(orb_data) > 0:
                orb_high = orb_data['high'].max()
                orb_low = orb_data['low'].min()
                orb_range = orb_high - orb_low
                if 4 < orb_range < 20:
                    daily_orbs[date] = {
                        'high': orb_high,
                        'low': orb_low,
                        'range': orb_range,
                        'mid': (orb_high + orb_low) / 2
                    }
    
    # Entry logic (09:30-10:30 = 570-630 min)
    if time_min < 570 or time_min > 630:
        continue
    
    if date not in daily_orbs:
        continue
    
    orb = daily_orbs[date]
    
    # Filters
    ema_ok = (row['ema20'] > row['ema50']) and (row['ema50'] > row['ema200'])
    vwap_ok = row['close'] > row['vwap']
    vol_ok = row['volume'] > row['avg_vol_20'] * 1.5
    disp_ok = row['body'] > row['avg_body_20'] * 2
    
    confluence = sum([ema_ok, vwap_ok, vol_ok, disp_ok])
    
    # Entry: breakout + retest
    if (row['close'] > orb['high'] and 
        row['low'] <= orb['mid'] and
        confluence >= 3 and
        ema_ok and vwap_ok):
        
        # Quick exit logic
        exit_high = df[df['date'] == date][time_min <= df['time_min']]['high'].max()
        exit_low = df[df['date'] == date][time_min <= df['time_min']]['low'].min()
        
        pnl_points = min(exit_high - row['close'], orb['range'] * 2)
        pnl = pnl_points * 50
        
        trades.append({
            'date': date,
            'time': row['datetime'],
            'entry': row['close'],
            'pnl': pnl,
            'confluence': confluence
        })

print(f"\n✓ Backtest complete: {len(trades)} trades found")

if len(trades) > 0:
    df_trades = pd.DataFrame(trades)
    total_pnl = df_trades['pnl'].sum()
    wins = len(df_trades[df_trades['pnl'] > 0])
    wr = wins / len(df_trades) if len(df_trades) > 0 else 0
    
    print(f"\nResults:")
    print(f"  Trades: {len(df_trades)}")
    print(f"  Wins: {wins} ({wr:.1%})")
    print(f"  Total P&L: ${total_pnl:.2f}")
    print(f"  Avg P&L: ${df_trades['pnl'].mean():.2f}")
    
    print(f"\nFirst 5 trades:")
    for i, trade in enumerate(df_trades.head(5).to_dict('records'), 1):
        print(f"  {i}. {trade['time']} @ {trade['entry']:.2f}: ${trade['pnl']:.2f} (C={trade['confluence']})")
else:
    print("  No trades generated - debugging needed")

print("\n" + "="*70 + "\n")
