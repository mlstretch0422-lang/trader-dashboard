import pandas as pd
from pathlib import Path
from datetime import datetime, time

# Config
RECON_PATH = Path("strat/data/reconstructed_trades_tagged.csv")
OHLC_PATH = Path("strat/frd_sample_futures_ES/ES_1min_sample.csv")
OUT_PATH = Path("trading_os/experiments/outputs/re_tagged_trades.csv")
ORB_START = "0800"  # fallback; parsed from strategy earlier could be used
ORB_END = "0815"
TOLERANCE_PCT = 0.15  # fraction of orb range to consider "near midpoint"


def hhmm_to_min(hhmm: str) -> int:
    hh = int(hhmm[:2]); mm = int(hhmm[2:]); return hh*60 + mm


def load_ohlc(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Try common datetime column names
    for c in ["datetime", "time", "timestamp"]:
        if c in df.columns:
            df['datetime'] = pd.to_datetime(df[c], errors='coerce')
            break
    if 'datetime' not in df.columns:
        # try first column
        df['datetime'] = pd.to_datetime(df.iloc[:,0], errors='coerce')
    df = df.dropna(subset=['datetime']).sort_values('datetime')
    return df


def compute_orb_for_day(df: pd.DataFrame, day, start_min, end_min):
    # df.datetime is timezone-naive or tz-aware; compare by date
    day_df = df[df['datetime'].dt.date == day]
    if day_df.empty:
        return None
    # compute hours
    # select rows where time between start_min and end_min
    mins = day_df['datetime'].dt.hour*60 + day_df['datetime'].dt.minute
    mask = (mins >= start_min) & (mins < end_min)
    if not mask.any():
        return None
    orb_section = day_df[mask]
    return {
        'orb_high': orb_section['high'].max(),
        'orb_low': orb_section['low'].min(),
        'orb_mid': (orb_section['high'].max() + orb_section['low'].min())/2.0,
        'orb_range': orb_section['high'].max() - orb_section['low'].min()
    }


def classify_trade(trade, ohlc_df, start_min, end_min):
    entry_time = pd.to_datetime(trade['entry_time'], errors='coerce')
    if pd.isna(entry_time):
        return 'unknown'
    day = entry_time.date()
    orb = compute_orb_for_day(ohlc_df, day, start_min, end_min)
    if orb is None:
        return 'no_orb_data'
    # Determine breakout time (first close > orb_high or < orb_low after ORB end)
    day_df = ohlc_df[ohlc_df['datetime'].dt.date == day]
    mins = day_df['datetime'].dt.hour*60 + day_df['datetime'].dt.minute
    after_orb = day_df[(mins >= end_min)]
    breakout_long = after_orb[after_orb['close'] > orb['orb_high']]
    breakout_short = after_orb[after_orb['close'] < orb['orb_low']]
    breakout_time = None
    breakout_dir = None
    if not breakout_long.empty:
        breakout_time = breakout_long['datetime'].iloc[0]
        breakout_dir = 'long'
    if not breakout_short.empty:
        bt = breakout_short['datetime'].iloc[0]
        if breakout_time is None or bt < breakout_time:
            breakout_time = bt
            breakout_dir = 'short'
    # If no breakout before entry, classify as 'no_breakout'
    if breakout_time is None or breakout_time > entry_time:
        # classify as direct breakout if entry itself is beyond orb edge
        if trade['entry_price'] >= orb['orb_high']:
            return 'break'
        if trade['entry_price'] <= orb['orb_low']:
            return 'break'
        return 'no_breakout'
    # There was a breakout before entry_time. Check if trade entry is near midpoint and after a pullback.
    entry_px = float(trade.get('entry_price', trade.get('entry_price', 0) or 0))
    tol = max(0.5, orb['orb_range'] * TOLERANCE_PCT)
    mid_low = orb['orb_mid'] - tol
    mid_high = orb['orb_mid'] + tol
    # If entry price is near midpoint, mark as retest
    if mid_low <= entry_px <= mid_high:
        return 'retest'
    # If entry_type indicates limit, lean retest
    etype = str(trade.get('entry_type', '')).lower()
    if 'limit' in etype or 'limit' in str(trade.get('entry_order_id','')).lower():
        return 'retest'
    # else break
    return 'break'


def main():
    ohlc = load_ohlc(OHLC_PATH)
    recon = pd.read_csv(RECON_PATH)
    start_min = hhmm_to_min(ORB_START)
    end_min = hhmm_to_min(ORB_END)
    results = []
    for _, r in recon.iterrows():
        cls = classify_trade(r, ohlc, start_min, end_min)
        row = r.to_dict()
        row['re_tag'] = cls
        results.append(row)
    out_df = pd.DataFrame(results)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_PATH, index=False)
    print('Wrote re-tagged trades to', OUT_PATH)
    # summary
    print(out_df['re_tag'].value_counts(dropna=False))

if __name__ == '__main__':
    main()
