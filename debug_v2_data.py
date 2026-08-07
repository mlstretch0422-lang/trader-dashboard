#!/usr/bin/env python3
"""
Debug V2 backtest - see what's actually happening
"""

import pandas as pd
import numpy as np

print("\n" + "="*70)
print("V2 BACKTEST DEBUG")
print("="*70)

# Load data
print("\n1. Loading data...")
df = pd.read_csv('ES_backtest_data.csv')
df['datetime'] = pd.to_datetime(df['datetime'])
df['hour'] = df['datetime'].dt.hour
df['minute'] = df['datetime'].dt.minute
df['date'] = df['datetime'].dt.date
df['time_min'] = df['hour'] * 60 + df['minute']

print(f"   ✓ Loaded {len(df):,} rows")
print(f"   Time range: {df['time_min'].min()}-{df['time_min'].max()} minutes")
print(f"   Date range: {df['date'].min()} to {df['date'].max()}")

# Check if we have the ORB window at all
orb_window = df[(df['time_min'] >= 480) & (df['time_min'] <= 495)]
print(f"   Bars in ORB window (8:00-8:15): {len(orb_window):,}")

if len(orb_window) == 0:
    print("   ⚠️  NO BARS IN ORB WINDOW!")
    print("   The data only contains market hours 9:30-16:00 ET")
    print("   Therefore we cannot calculate ORB")
    print("\n   SOLUTION: Calculate ORB from first 15 minutes of market instead")
    print("   (9:30-9:45 instead of 8:00-8:15)")
else:
    print(f"   ✓ ORB window available")

# Check entry window
entry_window = df[(df['time_min'] >= 570) & (df['time_min'] <= 630)]
print(f"   Bars in entry window (9:30-10:30): {len(entry_window):,}")

# Sample a few days to understand structure
print("\n2. Sampling a few days:")
for date in df['date'].unique()[:3]:
    day_data = df[df['date'] == date]
    print(f"\n   Date: {date}")
    print(f"     Total bars: {len(day_data)}")
    print(f"     Time range: {day_data['time_min'].min()}-{day_data['time_min'].max()} min")
    print(f"     Price range: {day_data['close'].min():.2f}-{day_data['close'].max():.2f}")
    print(f"     First 3 bars:")
    for idx, row in day_data.head(3).iterrows():
        print(f"       {row['time_min']:3d} min: O={row['open']:.2f} H={row['high']:.2f} L={row['low']:.2f} C={row['close']:.2f} V={row['volume']}")

print("\n" + "="*70)
print("KEY FINDINGS:")
print("="*70)

if len(orb_window) == 0:
    print("\n⚠️  CRITICAL ISSUE:")
    print("   The data contains ONLY market hours (9:30-16:00 ET)")
    print("   The ORB is typically calculated from premarket (8:00-8:15 ET)")
    print("   Since we don't have premarket data, we must:")
    print("     Option A: Use first 15 minutes of market (9:30-9:45) as ORB period")
    print("     Option B: Use different strategy approach")
    print("\n✅ RECOMMENDED: Option A - use 9:30-9:45 as ORB period")
else:
    print("\n✓ ORB window available in data")

print("\n" + "="*70 + "\n")
