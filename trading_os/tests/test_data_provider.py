import os

from src.integrations.data_provider import CSVDataProvider, AlpacaDataProvider, get_data_provider


def test_default_provider_is_csv():
    provider = get_data_provider()
    assert isinstance(provider, CSVDataProvider)


def test_alpaca_provider_uses_env_config(monkeypatch):
    monkeypatch.setenv("DATA_PROVIDER", "alpaca")
    monkeypatch.setenv("ALPACA_API_KEY", "test-key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "test-secret")

    provider = get_data_provider()

    assert isinstance(provider, AlpacaDataProvider)
    assert provider.api_key == "test-key"
    assert provider.secret_key == "test-secret"
