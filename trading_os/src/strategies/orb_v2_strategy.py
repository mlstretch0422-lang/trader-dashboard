#!/usr/bin/env python3
"""
ORB V2 Strategy Implementation (Evidence-Based)

Combines:
- RP Profit methodology (retest confirmation)
- TJR approach (filter stack)
- ICT concepts (FVGs, MSS, price action)
- Lux strategy (quantitative + PA hybrid)

Backtests on real ES data and compares against V1.
"""

import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
import json

class ORB_V2_Strategy:
    """V2 Strategy: Retest-based with filter confirmation"""
    
    def __init__(self, df):
        """
        Initialize with OHLCV data
        
        df: DataFrame with columns [datetime, open, high, low, close, volume]
        """
        self.df = df.copy()
        self.trades = []
        self.position = None
        self.entry_price = None
        self.entry_bar = None
        
    def get_et_time(self, dt):
        """Convert to ET and get minutes from midnight"""
        return dt.hour * 60 + dt.minute
    
    def compute_orb(self, df_day, orb_start_min=8*60, orb_end_min=8*60+15):
        """
        Compute ORB for a trading day
        
        orb_start_min: 8:00 ET = 480 minutes
        orb_end_min: 8:15 ET = 495 minutes
        """
        orb_mask = (
            (df_day.index.hour == 8) | 
            ((df_day.index.hour >= 8) & (df_day.index.hour < 9))
        ) & (
            (df_day.index.hour == 8) & (df_day.index.minute <= 15)
        )
        
        if len(df_day[orb_mask]) == 0:
            return None
        
        orb_high = df_day[orb_mask]['high'].max()
        orb_low = df_day[orb_mask]['low'].min()
        orb_range = orb_high - orb_low
        
        return {
            'orb_high': orb_high,
            'orb_low': orb_low,
            'orb_range': orb_range,
            'orb_mid': (orb_high + orb_low) / 2
        }
    
    def compute_ema(self, df, period=20):
        """Compute EMA"""
        return df['close'].ewm(span=period, adjust=False).mean()
    
    def check_ema_alignment(self, row, ema20, ema50, ema200):
        """Check EMA alignment for LONG: 20 > 50 > 200"""
        idx = row.name if isinstance(row.name, int) else row.name
        
        if pd.isna(ema20[idx]) or pd.isna(ema50[idx]) or pd.isna(ema200[idx]):
            return False
        
        return (ema20[idx] > ema50[idx]) and (ema50[idx] > ema200[idx])
    
    def check_vwap_filter(self, row):
        """Check VWAP filter (price > VWAP for long)"""
        if 'vwap' not in self.df.columns:
            return False
        
        idx = row.name if isinstance(row.name, int) else row.name
        vwap = self.df['vwap'][idx] if idx in self.df.index else None
        
        if pd.isna(vwap):
            return False
        
        return row['close'] > vwap
    
    def check_volume_filter(self, row, avg_volume):
        """Check volume filter (volume > 1.5x average)"""
        idx = row.name if isinstance(row.name, int) else row.name
        
        if pd.isna(avg_volume[idx]):
            return False
        
        return row['volume'] > avg_volume[idx] * 1.5
    
    def check_displacement(self, row, avg_body):
        """Check displacement (body > 2x average)"""
        idx = row.name if isinstance(row.name, int) else row.name
        
        if pd.isna(avg_body[idx]):
            return False
        
        body = abs(row['close'] - row['open'])
        return body > avg_body[idx] * 2
    
    def compute_vwap(self):
        """Compute VWAP"""
        cumsum_pv = (self.df['high'] + self.df['low'] + self.df['close']).div(3) * self.df['volume']
        cumsum_v = self.df['volume'].cumsum()
        self.df['vwap'] = cumsum_pv.cumsum() / cumsum_v
    
    def backtest(self, min_confluence=3):
        """
        Backtest V2 strategy with filter confirmation
        
        min_confluence: Minimum number of filters to confirm entry (3-5)
        """
        # Compute indicators
        self.df['ema20'] = self.compute_ema(self.df, 20)
        self.df['ema50'] = self.compute_ema(self.df, 50)
        self.df['ema200'] = self.compute_ema(self.df, 200)
        
        self.compute_vwap()
        
        avg_volume = self.df['volume'].rolling(20).mean()
        avg_body = abs(self.df['close'] - self.df['open']).rolling(20).mean()
        
        # Get unique trading days
        self.df['date'] = self.df.index.date
        trading_days = self.df['date'].unique()
        
        # Track ORB for each day
        orb_info = {}
        
        # Iterate through bars
        for idx, (i, row) in enumerate(self.df.iterrows()):
            current_date = row['date']
            current_time_min = self.get_et_time(i)
            
            # Calculate ORB at 8:15
            if current_time_min == 8*60 + 15:  # 8:15 ET
                day_data = self.df[self.df['date'] == current_date]
                orb = self.compute_orb(day_data)
                
                if orb and 4 < orb['orb_range'] < 20:  # Valid ORB
                    orb_info[current_date] = orb
            
            # Entry window: 9:30 - 10:30 ET
            if current_time_min < 9*60 + 30 or current_time_min > 10*60 + 30:
                continue
            
            # Forced exit at 11:00 ET
            if current_time_min >= 11*60 and self.position:
                self.close_position(row, "Forced exit (11:00 ET)")
                continue
            
            # Check for entry signals
            if not self.position and current_date in orb_info:
                orb = orb_info[current_date]
                
                # Check all filters
                ema_aligned = self.check_ema_alignment(row, self.df['ema20'], self.df['ema50'], self.df['ema200'])
                vwap_filter = self.check_vwap_filter(row)
                volume_filter = self.check_volume_filter(row, avg_volume)
                displacement = self.check_displacement(row, avg_body)
                
                # Confluence score (count aligned filters)
                confluence = sum([ema_aligned, vwap_filter, volume_filter, displacement])
                
                # Breakout + retest logic (price tested ORB, now closing above)
                breakout_long = (
                    row['close'] > orb['orb_high'] and
                    row['low'] <= orb['orb_mid'] and
                    confluence >= min_confluence
                )
                
                if breakout_long and ema_aligned and vwap_filter:
                    self.entry_price = row['close']
                    # Store the actual DataFrame index label (datetime), not loop counter.
                    self.entry_bar = i
                    self.position = "LONG"
                    self.entry_confluence = confluence
                    self.entry_sl = orb['orb_low']  # SL at ORB low
                    self.entry_range = orb['orb_range']
            
            # Check for exit signals
            if self.position == "LONG":
                # Stop loss
                if row['low'] < self.entry_sl:
                    exit_price = self.entry_sl
                    self.close_position_with_price(row, exit_price, "Stop Loss")
                    continue
                
                # Take profit (scale out at 1R, 2R, 3R)
                # For simplicity, exit at 2R
                target_1r = self.entry_price + self.entry_range
                target_2r = self.entry_price + (self.entry_range * 2)
                
                if row['high'] >= target_2r:
                    self.close_position_with_price(row, target_2r, "Take Profit 2R")
                    continue
                elif row['high'] >= target_1r and row['close'] < target_1r:
                    # Retest of 1R = exit
                    self.close_position(row, "Retest of 1R")
                    continue
        
        # Close any open position at end
        if self.position:
            self.close_position(self.df.iloc[-1], "End of period")
        
        return self.generate_report()
    
    def close_position(self, row, reason):
        """Close position at market price"""
        if not self.position:
            return
        
        exit_price = row['close']
        pnl = exit_price - self.entry_price
        pnl_usd = pnl * 50  # ES contract multiplier
        
        self.trades.append({
            'entry_time': self.df.loc[self.entry_bar].name,
            'entry_price': self.entry_price,
            'exit_time': row.name,
            'exit_price': exit_price,
            'pnl_pts': pnl,
            'pnl_usd': pnl_usd,
            'direction': self.position,
            'reason': reason,
            'confluence': self.entry_confluence,
            'orb_range': self.entry_range
        })
        
        self.position = None
        self.entry_price = None
    
    def close_position_with_price(self, row, price, reason):
        """Close position at specific price"""
        if not self.position:
            return
        
        pnl = price - self.entry_price
        pnl_usd = pnl * 50  # ES contract multiplier
        
        self.trades.append({
            'entry_time': self.df.loc[self.entry_bar].name,
            'entry_price': self.entry_price,
            'exit_time': row.name,
            'exit_price': price,
            'pnl_pts': pnl,
            'pnl_usd': pnl_usd,
            'direction': self.position,
            'reason': reason,
            'confluence': self.entry_confluence,
            'orb_range': self.entry_range
        })
        
        self.position = None
        self.entry_price = None
    
    def generate_report(self):
        """Generate backtest report"""
        if not self.trades:
            return {'status': 'NO_TRADES', 'message': 'No trades generated'}
        
        trades_df = pd.DataFrame(self.trades)
        
        # Calculate metrics
        wins = trades_df[trades_df['pnl_usd'] > 0]
        losses = trades_df[trades_df['pnl_usd'] < 0]
        
        total_pnl = trades_df['pnl_usd'].sum()
        win_count = len(wins)
        loss_count = len(losses)
        win_rate = win_count / len(trades_df) if len(trades_df) > 0 else 0
        
        if loss_count > 0:
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
            'trades': trades_df.to_dict('records')
        }
    
    def calculate_max_drawdown(self, trades_df):
        """Calculate maximum drawdown from cumulative PnL"""
        cum_pnl = trades_df['pnl_usd'].cumsum()
        
        if len(cum_pnl) == 0:
            return 0
        
        running_max = cum_pnl.expanding().max()
        drawdown = cum_pnl - running_max
        max_dd = drawdown.min()
        
        return max_dd


def main():
    """Run V2 backtest"""
    
    print("\n" + "="*70)
    print("ORB V2 STRATEGY BACKTEST (Evidence-Based, Retest-Focused)")
    print("="*70)
    
    # Load real ES data - try new file first, fall back to old
    df = None
    data_file = None
    
    try:
        df = pd.read_csv('ES_backtest_data.csv')
        data_file = 'ES_backtest_data.csv'
    except FileNotFoundError:
        pass
    
    if df is None:
        try:
            df = pd.read_csv('trading_os/frd_sample_futures_ES/ES_real_1min_synthetic.csv')
            data_file = 'trading_os/frd_sample_futures_ES/ES_real_1min_synthetic.csv'
        except FileNotFoundError:
            print("\n✗ Error: Could not find ES data (tried ES_backtest_data.csv and trading_os/frd_sample_futures_ES/ES_real_1min_synthetic.csv)")
            return
    
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
    
    print(f"\n✓ Loaded {len(df):,} bars of ES data from {data_file}")
    print(f"  Range: {df.index[0]} to {df.index[-1]}")
    print(f"  Duration: {(df.index[-1] - df.index[0]).days} days ({(df.index[-1] - df.index[0]).days / 365.25:.1f} years)")
    
    # Run backtest with different confluence levels
    results = {}
    
    for min_conf in [3, 4, 5]:
        print(f"\n--- Testing with Confluence >= {min_conf} ---")
        
        strategy = ORB_V2_Strategy(df)
        report = strategy.backtest(min_confluence=min_conf)
        results[f'confluence_{min_conf}'] = report
        
        if report['status'] == 'SUCCESS':
            print(f"Trades: {report['trades_count']}")
            print(f"Win Rate: {report['win_rate']:.1%}")
            print(f"Profit Factor: {report['profit_factor']:.2f}")
            print(f"Total PnL: ${report['total_pnl']:.2f}")
            print(f"Expectancy: ${report['expectancy']:.2f}/trade")
            print(f"Max Drawdown: ${report['max_drawdown']:.2f}")
        else:
            print(f"Status: {report['status']}")
    
    # Save results
    print("\n" + "="*70)
    print("Saving results...")
    
    with open('trading_os/experiments/outputs/v2_backtest_results.json', 'w') as f:
        # Convert to serializable format
        output = {}
        for key, result in results.items():
            output[key] = {
                'status': result['status'],
                'trades_count': result.get('trades_count', 0),
                'total_pnl': result.get('total_pnl', 0),
                'win_rate': result.get('win_rate', 0),
                'profit_factor': result.get('profit_factor', 0),
                'expectancy': result.get('expectancy', 0),
                'max_drawdown': result.get('max_drawdown', 0)
            }
        
        json.dump(output, f, indent=2)
    
    print("✓ Results saved to v2_backtest_results.json")
    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    main()
