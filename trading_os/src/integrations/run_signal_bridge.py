import json
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.integrations.alert_bridge import build_signal_payload, send_signal
from src.integrations.data_provider import get_data_provider


def main():
    provider = get_data_provider()
    df = provider.load()
    if df.empty:
        raise RuntimeError("No data available for signal generation")

    latest = df.iloc[-1]
    payload = build_signal_payload(
        df,
        side="long",
        entry_price=float(latest.get("close", 0.0)),
        confidence=0.8,
        note="Local ORB signal candidate",
    )

    output_path = Path(__file__).resolve().parent / "latest_signal.json"
    output_path.write_text(json.dumps(payload, indent=2))
    print(f"Wrote signal payload to {output_path}")

    result = send_signal(payload)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
