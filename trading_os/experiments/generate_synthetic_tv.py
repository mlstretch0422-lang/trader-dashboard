import pandas as pd
import numpy as np
from pathlib import Path

out = Path(__file__).parent / "synthetic_mes_tv.csv"
# Generate 2 days of 1-minute bars from 2026-06-29 06:00 UTC
rng = pd.date_range("2026-06-29 06:00", periods=2 * 6 * 60, freq='1min', tz='UTC')
np.random.seed(42)
price = 4000 + np.cumsum(np.random.randn(len(rng)) * 0.5)
open_p = price
high = open_p + np.abs(np.random.rand(len(rng)) * 0.6)
low = open_p - np.abs(np.random.rand(len(rng)) * 0.6)
close = open_p + np.random.randn(len(rng)) * 0.2
volume = np.random.randint(1, 100, size=len(rng))
df = pd.DataFrame({
    "datetime": rng.tz_convert('UTC').strftime('%Y-%m-%d %H:%M:%S'),
    "open": open_p,
    "high": high,
    "low": low,
    "close": close,
    "volume": volume,
})
df.to_csv(out, index=False)
print(f"Wrote synthetic TradingView-format CSV to: {out}")
