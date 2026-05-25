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


def test_yfinance_wrapper_includes_ticker_in_normalized_rows(monkeypatch):
    class FakeTicker:
        def history(self, start, end, auto_adjust):
            return [
                {
                    "Date": "2025-02-03",
                    "Open": 20.0,
                    "High": 21.0,
                    "Low": 19.5,
                    "Close": 20.5,
                    "Volume": 2200,
                }
            ]

    class FakeYFinanceModule:
        def Ticker(self, symbol):
            assert symbol == "AAPL"
            return FakeTicker()

    monkeypatch.setattr("src.market_data.yf", FakeYFinanceModule(), raising=False)

    provider = YFinanceMarketDataProvider()
    rows = provider.fetch_daily_prices("AAPL", "2025-02-01", "2025-02-10")

    assert rows == [
        {
            "date": "2025-02-03",
            "ticker": "AAPL",
            "open": 20.0,
            "high": 21.0,
            "low": 19.5,
            "close": 20.5,
            "volume": 2200,
        }
    ]


def test_yfinance_wrapper_accepts_dataframe_like_history(monkeypatch):
    class FakeFrame:
        def __iter__(self):
            return iter(["Open", "High", "Low", "Close", "Volume"])

        def reset_index(self):
            return self

        def to_dict(self, orient):
            assert orient == "records"
            return [
                {
                    "Date": "2025-03-03",
                    "Open": 30.0,
                    "High": 31.0,
                    "Low": 29.5,
                    "Close": 30.5,
                    "Volume": 3200,
                }
            ]

    class FakeTicker:
        def history(self, start, end, auto_adjust):
            return FakeFrame()

    class FakeYFinanceModule:
        def Ticker(self, symbol):
            assert symbol == "AAPL"
            return FakeTicker()

    monkeypatch.setattr("src.market_data.yf", FakeYFinanceModule(), raising=False)

    provider = YFinanceMarketDataProvider()

    assert provider.fetch_daily_prices("AAPL", "2025-03-01", "2025-03-10") == [
        {
            "date": "2025-03-03",
            "ticker": "AAPL",
            "open": 30.0,
            "high": 31.0,
            "low": 29.5,
            "close": 30.5,
            "volume": 3200,
        }
    ]
