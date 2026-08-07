import pandas as pd
from pathlib import Path

p = Path(__file__).parent.parent.parent / 'strat' / 'data' / 'reconstructed_trades_tagged.csv'
print('Reading', p)
df = pd.read_csv(p)

# Ensure numeric columns
if 'realized_pnl_usd' in df.columns:
    df['pnl'] = pd.to_numeric(df['realized_pnl_usd'], errors='coerce')
else:
    df['pnl'] = pd.to_numeric(df.get('realized_pnl_points', 0), errors='coerce')

# Basic overall metrics
total_trades = len(df)
net = df['pnl'].sum()
wins = df[df['pnl']>0]
losses = df[df['pnl']<=0]
win_rate = len(wins)/total_trades if total_trades else None
avg_win = wins['pnl'].mean() if not wins.empty else None
avg_loss = losses['pnl'].mean() if not losses.empty else None
average = df['pnl'].mean()
profit_factor = wins['pnl'].sum()/(-losses['pnl'].sum()) if losses['pnl'].sum()!=0 else None
expectancy = average

print('Overall metrics')
print('trades', total_trades)
print('net', net)
print('win_rate', win_rate)
print('avg_win', avg_win)
print('avg_loss', avg_loss)
print('profit_factor', profit_factor)
print('expectancy', expectancy)

# By trade_label
print('\nBy trade_label:')
for label, g in df.groupby('trade_label'):
    trades = len(g)
    net = g['pnl'].sum()
    wins = g[g['pnl']>0]
    losses = g[g['pnl']<=0]
    win_rate = len(wins)/trades if trades else None
    pf = wins['pnl'].sum()/(-losses['pnl'].sum()) if losses['pnl'].sum()!=0 else None
    print(f'label={label}: trades={trades}, net={net}, win_rate={win_rate}, pf={pf}')

# By outcome
print('\nBy outcome:')
print(df['outcome'].value_counts(dropna=False))

# By hour
print('\nBy entry_hour:')
print(df.groupby('entry_hour')['pnl'].agg(['count','sum','mean']))

# Save summary
out = Path(__file__).parent / 'outputs' / 'reconstructed_summary.csv'
out.parent.mkdir(exist_ok=True)
summary = {
    'total_trades': total_trades,
    'net': net,
    'win_rate': win_rate,
    'avg_win': avg_win,
    'avg_loss': avg_loss,
    'profit_factor': profit_factor,
    'expectancy': expectancy,
}
pd.Series(summary).to_csv(out)
print('\nWrote summary to', out)
