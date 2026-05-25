from src.market_data import YFinanceMarketDataProvider


def test_yfinance_wrapper_returns_clean_daily_price_rows(monkeypatch):
    class FakeTicker:
        def history(self, start, end, auto_adjust):
            assert start == "2025-01-01"
            assert end == "2025-01-10"
            assert auto_adjust is False
            return [
                {
                    "Date": "2025-01-02",
                    "Open": 10.0,
                    "High": 11.0,
                    "Low": 9.5,
                    "Close": 10.5,
                    "Volume": 1500,
                },
                {
                    "Date": "2025-01-03",
                    "Open": 10.5,
                    "High": 11.5,
                    "Low": 10.2,
                    "Close": 11.0,
                    "Volume": 1600,
                },
            ]

    class FakeYFinanceModule:
        def Ticker(self, symbol):
            assert symbol == "MSFT"
            return FakeTicker()

    monkeypatch.setattr("src.market_data.yf", FakeYFinanceModule(), raising=False)

    provider = YFinanceMarketDataProvider()

    assert provider.fetch_daily_prices("MSFT", "2025-01-01", "2025-01-10") == [
        {
            "date": "2025-01-02",
            "open": 10.0,
            "high": 11.0,
            "low": 9.5,
            "close": 10.5,
            "volume": 1500,
        },
        {
            "date": "2025-01-03",
            "open": 10.5,
            "high": 11.5,
            "low": 10.2,
            "close": 11.0,
            "volume": 1600,
        },
    ]
