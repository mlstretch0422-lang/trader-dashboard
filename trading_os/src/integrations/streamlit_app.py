import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.integrations.data_provider import get_data_provider
from src.strategies.clean_orb import compute_orb, generate_signals, summary_from_trades


st.set_page_config(page_title="Trader Dashboard", page_icon="📈", layout="wide")

st.title("Trader Dashboard")
st.caption("Local research dashboard for regime-aware ORB analysis")

provider = get_data_provider()

with st.spinner("Loading data..."):
    try:
        df = provider.load()
    except Exception as exc:
        st.error(f"Unable to load data: {exc}")
        st.stop()

if "datetime" in df.columns:
    df = df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"])

st.subheader("Data preview")
st.dataframe(df.head(10), use_container_width=True)

orb_map = compute_orb(df, 570, 585)
trades = generate_signals(df, orb_map, 570, 585, market_phase_filter=True, market_phase_threshold=0.5, use_vwap=False, use_ema=False)
summary = summary_from_trades(trades)

st.subheader("Strategy summary")
col1, col2, col3 = st.columns(3)
col1.metric("Trades", summary["trades"])
col2.metric("Win rate", f"{summary['win_rate'] * 100:.1f}%")
col3.metric("Dominant phase", summary["regime_summary"]["dominant_phase"])

st.json(summary)
