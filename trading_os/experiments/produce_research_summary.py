import sys
from pathlib import Path
import pandas as pd
import json

# Import existing utilities
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'strat' / 'src'))
from strat.metrics import compute_metrics

RECON = Path(__file__).parent.parent.parent / 'strat' / 'data' / 'reconstructed_trades_tagged.csv'
OUT_DIR = Path(__file__).parent / 'outputs'

def main():
    df = pd.read_csv(RECON)
    
    # ensure numeric pnl
    if 'realized_pnl_usd' in df.columns:
        df['pnl'] = pd.to_numeric(df['realized_pnl_usd'], errors='coerce')
    else:
        df['pnl'] = pd.to_numeric(df.get('realized_pnl_points', 0), errors='coerce')
    
    df['entry_time'] = pd.to_datetime(df['entry_time'], errors='coerce')
    df['date'] = df['entry_time'].dt.date
    df['hour'] = df['entry_time'].dt.hour
    
    # Overall summary
    overall_metrics = compute_metrics(df)
    
    # By trade_label
    by_label = {}
    for label, g in df.groupby('trade_label'):
        by_label[label] = compute_metrics(g)
    
    # By outcome
    by_outcome = {}
    for outcome, g in df.groupby('outcome'):
        by_outcome[outcome] = compute_metrics(g)
    
    # By entry_type
    by_entry_type = {}
    for et, g in df.groupby('entry_type'):
        by_entry_type[str(et)] = compute_metrics(g)
    
    # By exit_type
    by_exit_type = {}
    for ext, g in df.groupby('exit_type'):
        by_exit_type[str(ext)] = compute_metrics(g)
    
    # By hour
    by_hour = {}
    for h, g in df.groupby('hour'):
        by_hour[int(h)] = compute_metrics(g)
    
    # By symbol_short
    by_symbol = {}
    if 'symbol_short' in df.columns:
        for sym, g in df.groupby('symbol_short'):
            by_symbol[str(sym)] = compute_metrics(g)
    
    # By direction
    by_direction = {}
    if 'direction' in df.columns:
        for d, g in df.groupby('direction'):
            by_direction[str(d)] = compute_metrics(g)
    
    # Save summary JSON
    summary = {
        'overall': overall_metrics,
        'by_trade_label': by_label,
        'by_outcome': by_outcome,
        'by_entry_type': by_entry_type,
        'by_exit_type': by_exit_type,
        'by_hour': by_hour,
        'by_symbol': by_symbol,
        'by_direction': by_direction,
    }
    
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / 'trade_research_summary.json').write_text(json.dumps(summary, indent=2))
    print('Wrote trade_research_summary.json')
    
    # Print summary to console
    print('\n=== OVERALL METRICS ===')
    for k, v in overall_metrics.items():
        print(f'{k}: {v}')
    
    print('\n=== BY TRADE_LABEL ===')
    for label, m in by_label.items():
        print(f'{label}: trades={m.get("total_trades", 0)}, net={m.get("total_pnl", 0)}, pf={m.get("profit_factor", 0):.2f}, expectancy={m.get("expectancy", 0):.2f}')
    
    print('\n=== BY EXIT_TYPE ===')
    for ext, m in by_exit_type.items():
        print(f'{ext}: trades={m.get("total_trades", 0)}, net={m.get("total_pnl", 0)}, pf={m.get("profit_factor", 0):.2f}, expectancy={m.get("expectancy", 0):.2f}')

if __name__ == '__main__':
    main()
