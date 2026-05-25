"""Market data collection."""

try:
    import yfinance as yf
except ImportError:  # pragma: no cover - exercised through monkeypatch in tests.
    yf = None


class YFinanceMarketDataProvider:
    def fetch_daily_prices(self, symbol, start_date, end_date):
        if yf is None:
            raise RuntimeError("yfinance is not installed")

        history = yf.Ticker(symbol).history(
            start=start_date,
            end=end_date,
            auto_adjust=False,
        )

        return [self._normalize_row(symbol, row) for row in history]

    @staticmethod
    def _normalize_row(symbol, row):
        return {
            "date": str(row["Date"]),
            "open": row["Open"],
            "high": row["High"],
            "low": row["Low"],
            "close": row["Close"],
            "volume": row["Volume"],
        }
