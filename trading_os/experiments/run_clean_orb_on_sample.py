import pandas as pd
import sys
from pathlib import Path

# ensure local package path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from strategies.clean_orb import compute_orb, generate_signals, summary_from_trades

# sample file
ohlc = Path('strat/frd_sample_futures_ES/ES_1min_sample.csv')
df = pd.read_csv(ohlc)
# normalize datetime
if 'timestamp' in df.columns:
    df = df.rename(columns={'timestamp':'datetime'})

orb_map = compute_orb(df, orb_start_min=8*60, orb_end_min=8*60+15)
print('Computed ORBs for', len(orb_map), 'days')
trades = generate_signals(df, orb_map, orb_start_min=8*60, orb_end_min=8*60+15, use_vwap=False, use_ema=False)
print('Generated trades:', len(trades))
print(summary_from_trades(trades))

out = Path('trading_os/experiments/outputs/clean_orb_trades.csv')
out.parent.mkdir(parents=True, exist_ok=True)
if not trades.empty:
    trades.to_csv(out, index=False)
    print('Wrote trades to', out)
else:
    print('No trades written')
