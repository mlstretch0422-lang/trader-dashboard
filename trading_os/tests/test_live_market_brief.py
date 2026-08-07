import pandas as pd

from src.integrations.live_market_brief import build_market_brief


class DummyProvider:
    def __init__(self, df):
        self.df = df

    def load(self):
        return self.df


def test_build_market_brief_falls_back_to_local_data(monkeypatch):
    df = pd.DataFrame(
        [
            {
                "datetime": pd.Timestamp("2024-01-02 09:30"),
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1200,
            }
        ]
    )

    monkeypatch.setattr("src.integrations.live_market_brief.get_data_provider", lambda: DummyProvider(df))
    monkeypatch.setattr("src.integrations.live_market_brief.fetch_yahoo_quote", lambda symbol="ES=F": {})

    payload = build_market_brief()

    assert payload["market_snapshot"]["live_price"] == 100.5
    assert payload["market_snapshot"]["latest_close"] == 100.5
