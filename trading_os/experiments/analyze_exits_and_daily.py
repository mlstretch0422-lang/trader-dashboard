import pandas as pd
from pathlib import Path

p = Path('strat/data/reconstructed_trades_tagged.csv')
df = pd.read_csv(p)

# exit_type analysis
if 'realized_pnl_usd' in df.columns:
    df['pnl'] = pd.to_numeric(df['realized_pnl_usd'], errors='coerce')
else:
    df['pnl'] = pd.to_numeric(df.get('realized_pnl_points', 0), errors='coerce')

print('By exit_type:')
print(df.groupby('exit_type')['pnl'].agg(['count','sum','mean']))

# one-trade-per-day check
df['entry_time'] = pd.to_datetime(df['entry_time'], errors='coerce')
df['date'] = df['entry_time'].dt.date
trades_per_day = df.groupby('date').size()
print('\nTrades per day distribution:')
print(trades_per_day.value_counts().sort_index())

# days with >1 trade
multi = trades_per_day[trades_per_day>1]
print('\nDays with >1 trade count:', len(multi))

out = Path('trading_os/experiments/outputs/exit_daily_summary.csv')
out.parent.mkdir(parents=True, exist_ok=True)
summary = {
    'exit_type_counts': df['exit_type'].value_counts().to_dict(),
    'trades_per_day_counts': trades_per_day.value_counts().to_dict(),
    'multi_trade_days': len(multi)
}
import json
Path(out).write_text(json.dumps(summary, indent=2))
print('\nWrote', out)
