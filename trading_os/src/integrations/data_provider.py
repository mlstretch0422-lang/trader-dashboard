"""Simple data-provider abstractions for historical and live market data."""
import os
from typing import Optional

import pandas as pd


class CSVDataProvider:
    """Load OHLC data from a local CSV file."""

    def __init__(self, path: Optional[str] = None):
        if path:
            self.path = path
        else:
            configured = os.getenv("DATA_CSV_PATH")
            if configured:
                self.path = configured
            else:
                candidates = [
                    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ES_backtest_data.market_hours_only.backup.csv")),
                    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "ES_backtest_data.csv")),
                ]
                self.path = next((candidate for candidate in candidates if os.path.exists(candidate)), candidates[0])

    def load(self) -> pd.DataFrame:
        df = pd.read_csv(self.path)
        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"])
        return df


class AlpacaDataProvider:
    """Optional data provider for live or historical market data via Alpaca."""

    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ALPACA_API_KEY")
        self.secret_key = secret_key or os.getenv("ALPACA_SECRET_KEY")

    def load(self) -> pd.DataFrame:
        if not self.api_key or not self.secret_key:
            raise RuntimeError("Alpaca credentials are not configured")
        raise NotImplementedError("Alpaca integration requires the SDK and runtime credentials")


def get_data_provider() -> object:
    provider_name = os.getenv("DATA_PROVIDER", "csv").lower()
    if provider_name == "alpaca":
        return AlpacaDataProvider()
    return CSVDataProvider()
