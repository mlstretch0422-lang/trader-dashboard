#!/usr/bin/env python3
"""
ORB V2 Strategy - Simplified Backtest

Simplified version focused on core logic:
1. Calculate ORB (08:00-08:15 ET) per day
2. Generate entries 09:30+ ET on retest + filters
3. Track P&L and metrics
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
import json

class ORB_V2_Backtest:
    def __init__(self, df):
        self.df = df.copy()
        self.trades = []
        self.daily_orbs = {}
        
    def get_time_minutes(self, dt):
        """Convert datetime to minutes from midnight"""
        return dt.hour * 60 + dt.minute
    
    def backtest(self):
        """Run simplified V2 backtest"""
        
        # Add required columns
        self.df['time_min'] = self.df.index.hour * 60 + self.df.index.minute
        self.df['date'] = self.df.index.date
        self.df['body'] = abs(self.df['close'] - self.df['open'])
        
        # Calculate indicators (once for whole dataset)
        print("Computing indicators...")
        self.df['ema20'] = self.df['close'].ewm(span=20, adjust=False).mean()
        self.df['ema50'] = self.df['close'].ewm(span=50, adjust=False).mean()
        self.df['ema200'] = self.df['close'].ewm(span=200, adjust=False).mean()
        self.df['avg_vol_20'] = self.df['volume'].rolling(20).mean()
        self.df['avg_body_20'] = self.df['body'].rolling(20).mean()
        
        # Compute VWAP daily (reset each day)
        print("Computing VWAP...")
        vwap_list = []
        for date in self.df['date'].unique():
            day_data = self.df[self.df['date'] == date]
            typical_price = (day_data['high'] + day_data['low'] + day_data['close']) / 3
            cumsum_pv = (typical_price * day_data['volume']).cumsum()
            cumsum_v = day_data['volume'].cumsum()
            daily_vwap = cumsum_pv / cumsum_v
            vwap_list.append(daily_vwap)
        
        self.df['vwap'] = pd.concat(vwap_list).sort_index()
        
        # Forward fill NaN values from early rolling windows
        self.df = self.df.fillna(method='ffill')
        
        print(f"Processing {len(self.df):,} bars...")
        
        # Track state
        in_position = False
        entry_price = None
        entry_idx = None
        entry_date = None
        orb_low = None
        
        trades_found = 0
        
        # Iterate through bars
        for i in range(len(self.df)):
            row = self.df.iloc[i]
            current_date = row['date']
            time_min = row['time_min']
            
            # ORB Calculation: 08:00-08:15 ET (480-495 minutes)
            if 480 <= time_min <= 495:
                if current_date not in self.daily_orbs:
                    day_data = self.df[self.df['date'] == current_date]
                    orb_mask = (day_data['time_min'] >= 480) & (day_data['time_min'] <= 495)
                    if len(day_data[orb_mask]) > 0:
                        orb_high = day_data[orb_mask]['high'].max()
                        orb_low = day_data[orb_mask]['low'].min()
                        orb_range = orb_high - orb_low
                        
                        # Valid ORB: 4-20 points
                        if 4 < orb_range < 20:
                            self.daily_orbs[current_date] = {
                                'high': orb_high,
                                'low': orb_low,
                                'range': orb_range,
                                'mid': (orb_high + orb_low) / 2
                            }
            
            # Entry window: 09:30-10:30 ET (570-630 minutes)
            # Skip if time outside entry window or already in position
            if time_min < 570 or time_min > 630 or in_position:
                continue
            
            # Skip if no valid ORB for today
            if current_date not in self.daily_orbs:
                continue
            
            orb = self.daily_orbs[current_date]
            
            # Check filters
            ema_aligned = (row['ema20'] > row['ema50']) and (row['ema50'] > row['ema200'])
            vwap_filter = row['close'] > row['vwap']
            vol_filter = row['volume'] > row['avg_vol_20'] * 1.5
            displacement = row['body'] > row['avg_body_20'] * 2
            
            confluence = sum([ema_aligned, vwap_filter, vol_filter, displacement])
            
            # Entry logic: Breakout + retest
            # Long: close > ORB high AND price has touched ORB mid (retest)
            breakout_long = (
                (row['close'] > orb['high']) and
                (row['low'] <= orb['mid']) and
                confluence >= 3 and
                ema_aligned and
                vwap_filter
            )
            
            if breakout_long:
                in_position = True
                entry_price = row['close']
                entry_idx = i
                entry_date = current_date
                sl_price = orb['low']
                tp_2r = entry_price + (orb['range'] * 2)  # 2R target
                trades_found += 1
                
                if trades_found <= 5:  # Print first few
                    print(f"  Entry #{trades_found}: {row.name} @ {entry_price:.2f}, Confluence: {confluence}, ORB: {orb['range']:.2f}")
            
            # Exit logic
            if in_position and current_date == entry_date:
                # Stop loss
                if row['low'] < sl_price:
                    pnl = sl_price - entry_price
                    pnl_usd = pnl * 50
                    self.trades.append({
                        'entry': self.df.index[entry_idx],
                        'entry_price': entry_price,
                        'exit': row.name,
                        'exit_price': sl_price,
                        'pnl': pnl,
                        'pnl_usd': pnl_usd,
                        'reason': 'SL'
                    })
                    in_position = False
                
                # Take profit at 2R
                elif row['high'] >= tp_2r:
                    pnl = tp_2r - entry_price
                    pnl_usd = pnl * 50
                    self.trades.append({
                        'entry': self.df.index[entry_idx],
                        'entry_price': entry_price,
                        'exit': row.name,
                        'exit_price': tp_2r,
                        'pnl': pnl,
                        'pnl_usd': pnl_usd,
                        'reason': 'TP'
                    })
                    in_position = False
                
                # Forced exit at 16:00 ET
                elif time_min >= 960:
                    pnl = row['close'] - entry_price
                    pnl_usd = pnl * 50
                    self.trades.append({
                        'entry': self.df.index[entry_idx],
                        'entry_price': entry_price,
                        'exit': row.name,
                        'exit_price': row['close'],
                        'pnl': pnl,
                        'pnl_usd': pnl_usd,
                        'reason': 'EOD'
                    })
                    in_position = False
        
        # Close any open position
        if in_position:
            last_row = self.df.iloc[-1]
            pnl = last_row['close'] - entry_price
            pnl_usd = pnl * 50
            self.trades.append({
                'entry': self.df.index[entry_idx],
                'entry_price': entry_price,
                'exit': last_row.name,
                'exit_price': last_row['close'],
                'pnl': pnl,
                'pnl_usd': pnl_usd,
                'reason': 'END'
            })
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate backtest report"""
        if not self.trades:
            return {
                'status': 'NO_TRADES',
                'trades_count': 0,
                'message': 'No trades generated'
            }
        
        trades_df = pd.DataFrame(self.trades)
        
        wins = trades_df[trades_df['pnl_usd'] > 0]
        losses = trades_df[trades_df['pnl_usd'] < 0]
        
        total_pnl = trades_df['pnl_usd'].sum()
        win_count = len(wins)
        loss_count = len(losses)
        win_rate = win_count / len(trades_df) if len(trades_df) > 0 else 0
        
        if loss_count > 0 and len(losses) > 0:
            pf = wins['pnl_usd'].sum() / abs(losses['pnl_usd'].sum())
        else:
            pf = 999 if win_count > 0 else 0
        
        avg_win = wins['pnl_usd'].mean() if len(wins) > 0 else 0
        avg_loss = losses['pnl_usd'].mean() if len(losses) > 0 else 0
        
        expectancy = trades_df['pnl_usd'].mean()
        max_dd = self.calculate_max_drawdown(trades_df)
        
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
            'max_drawdown': max_dd,
            'sample_trades': trades_df.head(10).to_dict('records')
        }
    
    def calculate_max_drawdown(self, trades_df):
        """Calculate max drawdown"""
        cum_pnl = trades_df['pnl_usd'].cumsum()
        if len(cum_pnl) == 0:
            return 0
        running_max = cum_pnl.expanding().max()
        drawdown = cum_pnl - running_max
        return drawdown.min()


def main():
    print("\n" + "="*70)
    print("ORB V2 BACKTEST - 16 YEARS ES DATA")
    print("="*70)
    
    # Load data
    try:
        df = pd.read_csv('ES_backtest_data.csv')
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
    except:
        print("✗ Could not load ES_backtest_data.csv")
        return
    
    print(f"\n✓ Loaded {len(df):,} bars")
    print(f"  Range: {df.index[0]} to {df.index[-1]}")
    print(f"  Duration: {(df.index[-1] - df.index[0]).days / 365.25:.1f} years")
    
    # Run backtest
    print("\nRunning backtest...")
    backtest = ORB_V2_Backtest(df)
    report = backtest.backtest()
    
    # Display results
    print("\n" + "="*70)
    if report['status'] == 'SUCCESS':
        print(f"✓ RESULTS (Confluence >= 3)")
        print("="*70)
        print(f"Trades: {report['trades_count']}")
        print(f"  Wins: {report['win_count']} ({report['win_rate']:.1%})")
        print(f"  Losses: {report['loss_count']}")
        print(f"\nProfitability:")
        print(f"  Profit Factor: {report['profit_factor']:.2f}")
        print(f"  Total P&L: ${report['total_pnl']:.2f}")
        print(f"  Avg Win: ${report['avg_win']:.2f}")
        print(f"  Avg Loss: ${report['avg_loss']:.2f}")
        print(f"  Expectancy: ${report['expectancy']:.2f}/trade")
        print(f"\nRisk:")
        print(f"  Max Drawdown: ${report['max_drawdown']:.2f}")
        
        print(f"\nSample Trades (first 10):")
        for i, trade in enumerate(report['sample_trades'][:10], 1):
            print(f"  {i}. {trade['reason']:3} @ {trade['entry_price']:7.2f} → {trade['exit_price']:7.2f} | P&L: ${trade['pnl_usd']:7.2f}")
    else:
        print(f"Status: {report['status']}")
        print(f"Message: {report['message']}")
    
    # Save results
    print("\nSaving results...")
    with open('trading_os/experiments/outputs/v2_backtest_results.json', 'w') as f:
        json.dump({k: v for k, v in report.items() if k != 'sample_trades'}, f, indent=2, default=str)
    
    print("✓ Results saved to v2_backtest_results.json")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
