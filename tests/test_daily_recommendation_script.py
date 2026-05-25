from pathlib import Path
import runpy

from src.database import get_recommendations
from src.recommendations import generate_daily_recommendations


def test_generate_daily_recommendations_from_ticker_list(tmp_path):
    db_path = tmp_path / "research.db"
    tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "SPY"]
    price_history = {
        "AAPL": _price_rows(100.0, 2.0, 1000),
        "MSFT": _price_rows(100.0, 1.5, 1000),
        "NVDA": _price_rows(100.0, 3.0, 1000),
        "GOOGL": _price_rows(100.0, 1.0, 1000),
        "AMZN": _price_rows(100.0, 0.5, 1000),
        "META": _price_rows(100.0, 2.5, 1000),
        "TSLA": _price_rows(100.0, -0.5, 1000),
        "SPY": _price_rows(100.0, 0.2, 1000),
    }

    recommendations = generate_daily_recommendations(
        tickers=tickers,
        benchmark_ticker="SPY",
        start_date="2025-01-01",
        end_date="2025-01-20",
        db_path=db_path,
        price_history_by_ticker=price_history,
    )

    assert recommendations == [
        {
            "ticker": "NVDA",
            "rank": 1,
            "score": 0.5333860809321367,
            "entry_price": 157.0,
            "strategy_version": "v1",
            "reasons": [
                "return_20d contributed 0.285",
                "return_5d contributed 0.03103448275862069",
                "volume_ratio_20d contributed 0.21735159817351601",
            ],
            "risk_notes": ["20-day volatility is elevated"],
        },
        {
            "ticker": "META",
            "rank": 2,
            "score": 0.4821243254462433,
            "entry_price": 147.5,
            "strategy_version": "v1",
            "reasons": [
                "return_20d contributed 0.2375",
                "return_5d contributed 0.02727272727272727",
                "volume_ratio_20d contributed 0.21735159817351601",
            ],
            "risk_notes": ["20-day volatility is elevated"],
        },
        {
            "ticker": "AAPL",
            "rank": 3,
            "score": 0.43042852125043907,
            "entry_price": 138.0,
            "strategy_version": "v1",
            "reasons": [
                "return_20d contributed 0.19",
                "return_5d contributed 0.023076923076923078",
                "volume_ratio_20d contributed 0.21735159817351601",
            ],
            "risk_notes": ["20-day volatility is elevated"],
        },
        {
            "ticker": "MSFT",
            "rank": 4,
            "score": 0.3782189451122915,
            "entry_price": 128.5,
            "strategy_version": "v1",
            "reasons": [
                "return_20d contributed 0.1425",
                "return_5d contributed 0.01836734693877551",
                "volume_ratio_20d contributed 0.21735159817351601",
            ],
            "risk_notes": ["20-day volatility is elevated"],
        },
        {
            "ticker": "GOOGL",
            "rank": 5,
            "score": 0.3253950764343856,
            "entry_price": 119.0,
            "strategy_version": "v1",
            "reasons": [
                "return_20d contributed 0.095",
                "return_5d contributed 0.013043478260869565",
                "volume_ratio_20d contributed 0.21735159817351601",
            ],
            "risk_notes": ["20-day volatility is elevated"],
        },
    ]

    assert get_recommendations(db_path, trading_date="2025-01-20") == [
        {
            "trading_date": "2025-01-20",
            "symbol": "NVDA",
            "score": 0.5333860809321367,
            "rank": 1,
            "strategy_version": "v1",
        },
        {
            "trading_date": "2025-01-20",
            "symbol": "META",
            "score": 0.4821243254462433,
            "rank": 2,
            "strategy_version": "v1",
        },
        {
            "trading_date": "2025-01-20",
            "symbol": "AAPL",
            "score": 0.43042852125043907,
            "rank": 3,
            "strategy_version": "v1",
        },
        {
            "trading_date": "2025-01-20",
            "symbol": "MSFT",
            "score": 0.3782189451122915,
            "rank": 4,
            "strategy_version": "v1",
        },
        {
            "trading_date": "2025-01-20",
            "symbol": "GOOGL",
            "score": 0.3253950764343856,
            "rank": 5,
            "strategy_version": "v1",
        },
    ]


def test_manual_script_exists_and_uses_default_ticker_list(monkeypatch, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/generate_daily_recommendations.py"
    captured = {}

    def fake_generate_daily_recommendations(**kwargs):
        captured.update(kwargs)
        return []

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr(
        "src.recommendations.generate_daily_recommendations",
        fake_generate_daily_recommendations,
    )

    runpy.run_path(str(script_path), run_name="__main__")

    assert captured == {
        "tickers": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "SPY"],
        "benchmark_ticker": "SPY",
        "start_date": captured["start_date"],
        "end_date": captured["end_date"],
        "db_path": Path("data/stock_research.db"),
    }


def test_generate_daily_recommendations_excludes_benchmark_ticker(tmp_path):
    db_path = tmp_path / "research.db"
    tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "SPY"]
    price_history = {
        "AAPL": _price_rows(100.0, 2.0, 1000),
        "MSFT": _price_rows(100.0, 1.5, 1000),
        "NVDA": _price_rows(100.0, 3.0, 1000),
        "GOOGL": _price_rows(100.0, 1.0, 1000),
        "AMZN": _price_rows(100.0, 0.5, 1000),
        "META": _price_rows(100.0, 2.5, 1000),
        "TSLA": _price_rows(100.0, -0.5, 1000),
        "SPY": _price_rows(100.0, 10.0, 1000),
    }

    recommendations = generate_daily_recommendations(
        tickers=tickers,
        benchmark_ticker="SPY",
        start_date="2025-01-01",
        end_date="2025-01-20",
        db_path=db_path,
        price_history_by_ticker=price_history,
    )

    assert all(recommendation["ticker"] != "SPY" for recommendation in recommendations)


def _price_rows(start_close, close_step, start_volume):
    rows = []
    close = start_close
    volume = start_volume

    for day in range(20):
        rows.append(
            {
                "date": f"2025-01-{day + 1:02d}",
                "open": close - 0.5,
                "high": close + 1.0,
                "low": close - 1.0,
                "close": close,
                "volume": volume,
                "ticker": "IGNORED",
            }
        )
        close += close_step
        volume += 10

    return rows
