#!/usr/bin/env python3
"""
ORB V2 Strategy - CORRECTED (Uses market hours ORB)

Key Fix:
- Data only has market hours (9:30-16:00 ET)
- Use 9:30-9:45 as ORB period (instead of 8:00-8:15)
- Entry window: 9:45-10:30 ET (after ORB confirmed)
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime

class ORB_V2_Fixed:
    def __init__(self, df):
        self.df = df.copy()
        self.trades = []
        
    def run(self):
        print("\n" + "="*70)
        print("ORB V2 BACKTEST - FIXED (Market Hours ORB)")
        print("="*70)
        
        # Prepare data
        print("\n1. Preparing data...")
        self.df['datetime'] = pd.to_datetime(self.df['datetime'])
        self.df['hour'] = self.df['datetime'].dt.hour
        self.df['minute'] = self.df['datetime'].dt.minute
        self.df['date'] = self.df['datetime'].dt.date
        self.df['time_min'] = self.df['hour'] * 60 + self.df['minute']
        self.df['body'] = abs(self.df['close'] - self.df['open'])
        
        print(f"   ✓ {len(self.df):,} bars loaded")
        print(f"   ✓ Time range: {self.df['time_min'].min()}-{self.df['time_min'].max()} min (9:30-16:00 ET)")
        
        # Compute indicators
        print("2. Computing indicators...")
        self.df['ema20'] = self.df['close'].ewm(span=20, adjust=False).mean()
        self.df['ema50'] = self.df['close'].ewm(span=50, adjust=False).mean()
        self.df['ema200'] = self.df['close'].ewm(span=200, adjust=False).mean()
        self.df['avg_vol_20'] = self.df['volume'].rolling(20).mean()
        self.df['avg_body_20'] = self.df['body'].rolling(20).mean()
        self.df = self.df.ffill()  # Forward fill NaN values
        
        print(f"   ✓ EMA20, EMA50, EMA200, avg volume, avg body computed")
        
        # Compute VWAP per day
        print("3. Computing VWAP...")
        vwap_dict = {}
        dates = self.df['date'].unique()
        for i, date in enumerate(dates):
            if i % 1000 == 0 and i > 0:
                print(f"   Processing dates... {i:,}/{len(dates):,}")
            
            day_mask = self.df['date'] == date
            day_data = self.df[day_mask]
            if len(day_data) > 0:
                tp = (day_data['high'] + day_data['low'] + day_data['close']) / 3
                pv = tp * day_data['volume']
                cum_pv = pv.cumsum()
                cum_v = day_data['volume'].cumsum()
                day_vwap = cum_pv / cum_v
                
                for idx, val in zip(day_data.index, day_vwap):
                    vwap_dict[idx] = val
        
        self.df['vwap'] = self.df.index.map(lambda x: vwap_dict.get(x, np.nan))
        self.df['vwap'] = self.df['vwap'].ffill()
        print(f"   ✓ VWAP computed for all {len(dates):,} dates")
        
        # Backtest
        print("4. Running backtest...")
        self.df = self.df.sort_values('datetime').reset_index(drop=True)
        
        daily_orbs = {}
        in_position = False
        entry_price = None
        entry_idx = None
        entry_date = None
        entry_conf = None
        
        for i, row in self.df.iterrows():
            if i % 100000 == 0 and i > 0:
                print(f"   {i:,}/{len(self.df):,} bars... {len(self.trades)} trades so far")
            
            date = row['date']
            time_min = row['time_min']
            
            # ORB Calculation: 9:30-9:45 ET (570-585 min)
            if 570 <= time_min <= 585:
                if date not in daily_orbs:
                    day_mask = (self.df['date'] == date) & (self.df['time_min'] >= 570) & (self.df['time_min'] <= 585)
                    orb_data = self.df[day_mask]
                    
                    if len(orb_data) > 0:
                        orb_high = orb_data['high'].max()
                        orb_low = orb_data['low'].min()
                        orb_range = orb_high - orb_low
                        
                        # Valid ORB: 4-20 points range
                        if 4 < orb_range < 20:
                            daily_orbs[date] = {
                                'high': orb_high,
                                'low': orb_low,
                                'range': orb_range,
                                'mid': (orb_high + orb_low) / 2
                            }
            
            # Entry window: 9:45-11:00 ET (585-660 min)
            if time_min < 585 or time_min > 660:
                continue
            
            if in_position:
                continue
            
            if date not in daily_orbs:
                continue
            
            orb = daily_orbs[date]
            
            # Filter checks
            ema_ok = (row['ema20'] > row['ema50']) and (row['ema50'] > row['ema200'])
            vwap_ok = row['close'] > row['vwap']
            vol_ok = row['volume'] > row['avg_vol_20'] * 1.5
            disp_ok = row['body'] > row['avg_body_20'] * 2
            
            confluence = sum([ema_ok, vwap_ok, vol_ok, disp_ok])
            
            # Entry: Breakout + Retest
            # Long: close breaks above ORB high AND price has retested ORB mid
            breakout_long = (
                (row['close'] > orb['high']) and
                (row['low'] <= orb['mid']) and
                confluence >= 3 and
                ema_ok and
                vwap_ok
            )
            
            if breakout_long:
                in_position = True
                entry_price = row['close']
                entry_idx = i
                entry_date = date
                entry_conf = confluence
                sl_price = orb['low']
                tp_price = entry_price + (orb['range'] * 2)  # 2R target
                
                # Now find exit for this trade
                # Look ahead in same day
                remaining = self.df[(self.df['date'] == date) & (self.df.index > i)]
                
                if len(remaining) > 0:
                    # Check for stop loss hit first
                    sl_hit = remaining[remaining['low'] <= sl_price]
                    # Check for TP hit
                    tp_hit = remaining[remaining['high'] >= tp_price]
                    # Check for EOD (16:00 = 960 min)
                    eod_hit = remaining[remaining['time_min'] >= 960]
                    
                    exit_price = None
                    exit_type = None
                    
                    if len(sl_hit) > 0:
                        exit_price = sl_price
                        exit_type = 'SL'
                    elif len(tp_hit) > 0:
                        exit_price = tp_price
                        exit_type = 'TP'
                    elif len(eod_hit) > 0:
                        exit_row = eod_hit.iloc[0]
                        exit_price = exit_row['close']
                        exit_type = 'EOD'
                    else:
                        # Last bar of day
                        exit_price = remaining.iloc[-1]['close']
                        exit_type = 'END'
                    
                    if exit_price:
                        pnl = exit_price - entry_price
                        pnl_usd = pnl * 50  # $50 per point for 1 ES contract
                        
                        self.trades.append({
                            'entry_time': row['datetime'],
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'exit_type': exit_type,
                            'pnl': pnl,
                            'pnl_usd': pnl_usd,
                            'confluence': confluence,
                            'orb_range': orb['range']
                        })
                    
                    in_position = False
        
        return self.generate_report()
    
    def generate_report(self):
        if not self.trades:
            return {'status': 'NO_TRADES', 'trades_count': 0}
        
        trades_df = pd.DataFrame(self.trades)
        
        wins = trades_df[trades_df['pnl_usd'] > 0]
        losses = trades_df[trades_df['pnl_usd'] < 0]
        
        total_pnl = trades_df['pnl_usd'].sum()
        win_count = len(wins)
        loss_count = len(losses)
        win_rate = win_count / len(trades_df) if len(trades_df) > 0 else 0
        
        if loss_count > 0:
            pf = abs(wins['pnl_usd'].sum()) / abs(losses['pnl_usd'].sum()) if abs(losses['pnl_usd'].sum()) > 0 else 999
        else:
            pf = 999 if win_count > 0 else 0
        
        avg_win = wins['pnl_usd'].mean() if len(wins) > 0 else 0
        avg_loss = losses['pnl_usd'].mean() if len(losses) > 0 else 0
        expectancy = trades_df['pnl_usd'].mean()
        
        return {
            'status': 'SUCCESS',
            'trades_count': len(trades_df),
            'total_pnl': total_pnl,
            'win_count': win_count,
            'loss_count': loss_count,
            'win_rate': win_rate,
            'profit_factor': pf,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'expectancy': expectancy,
            'sample_trades': trades_df.head(20).to_dict('records')
        }


def main():
    # Load data
    print("\nLoading data...")
    df = pd.read_csv('ES_backtest_data.csv')
    
    # Run backtest
    backtest = ORB_V2_Fixed(df)
    report = backtest.run()
    
    # Display results
    print("\n" + "="*70)
    if report['status'] == 'SUCCESS':
        print(f"✅ BACKTEST COMPLETE")
        print("="*70)
        print(f"\nTrades: {report['trades_count']}")
        print(f"  Wins: {report['win_count']} ({report['win_rate']:.1%})")
        print(f"  Losses: {report['loss_count']}")
        print(f"\nProfitability:")
        print(f"  Profit Factor: {report['profit_factor']:.2f}")
        print(f"  Total P&L: ${report['total_pnl']:.2f}")
        print(f"  Avg Win: ${report['avg_win']:.2f}")
        print(f"  Avg Loss: ${report['avg_loss']:.2f}")
        print(f"  Expectancy: ${report['expectancy']:.2f}/trade")
        
        print(f"\nComparison to V1:")
        print(f"  V1 Win Rate: 31.6%, PF: 1.78")
        print(f"  V2 Win Rate: {report['win_rate']:.1%}, PF: {report['profit_factor']:.2f}")
        
        print(f"\nSample trades (first 10):")
        for i, trade in enumerate(report['sample_trades'][:10], 1):
            print(f"  {i:2d}. {trade['exit_type']:3s} @ {trade['entry_price']:7.2f} → {trade['exit_price']:7.2f} | ${trade['pnl_usd']:7.2f} (C={trade['confluence']})")
    else:
        print(f"Status: {report['status']}")
    
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
