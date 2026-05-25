from pathlib import Path
import runpy

from src.database import initialize_database, save_recommendations
from src.review import generate_weekly_review


def test_generate_weekly_review_from_saved_recommendations(tmp_path):
    db_path = tmp_path / "research.db"
    initialize_database(db_path)
    save_recommendations(
        db_path,
        trading_date="2025-01-03",
        strategy_version="v1",
        recommendations=[
            {"ticker": "AAPL", "score": 0.9, "rank": 1},
            {"ticker": "MSFT", "score": 0.8, "rank": 2},
        ],
    )

    provider = FakeMarketDataProvider(
        {
            "AAPL": [
                {"date": "2025-01-03", "close": 100.0},
                {"date": "2025-01-10", "close": 110.0},
            ],
            "MSFT": [
                {"date": "2025-01-03", "close": 200.0},
                {"date": "2025-01-10", "close": 190.0},
            ],
            "SPY": [
                {"date": "2025-01-03", "close": 500.0},
                {"date": "2025-01-10", "close": 510.0},
            ],
        }
    )

    review = generate_weekly_review(
        db_path=db_path,
        start_date="2025-01-01",
        end_date="2025-01-10",
        benchmark_ticker="SPY",
        provider=provider,
    )

    assert review == {
        "summary": {
            "reviewed_count": 2,
            "win_count": 1,
            "loss_count": 1,
            "win_rate": 0.5,
            "average_return": 0.025,
            "average_benchmark_return": 0.02,
            "average_excess_return": 0.005000000000000001,
            "best_ticker": "AAPL",
            "worst_ticker": "MSFT",
        },
        "rows": [
            {
                "ticker": "AAPL",
                "entry_price": 100.0,
                "exit_price": 110.0,
                "return_pct": 0.1,
                "benchmark_return_pct": 0.02,
                "excess_return_pct": 0.08,
                "is_win": True,
            },
            {
                "ticker": "MSFT",
                "entry_price": 200.0,
                "exit_price": 190.0,
                "return_pct": -0.05,
                "benchmark_return_pct": 0.02,
                "excess_return_pct": -0.07,
                "is_win": False,
            },
        ],
    }


def test_generate_weekly_review_handles_no_recommendations_gracefully(tmp_path):
    db_path = tmp_path / "research.db"
    initialize_database(db_path)

    provider = FakeMarketDataProvider({})

    review = generate_weekly_review(
        db_path=db_path,
        start_date="2025-01-01",
        end_date="2025-01-10",
        benchmark_ticker="SPY",
        provider=provider,
    )

    assert review == {
        "summary": {
            "reviewed_count": 0,
            "win_count": 0,
            "loss_count": 0,
            "win_rate": 0.0,
            "average_return": 0.0,
            "average_benchmark_return": 0.0,
            "average_excess_return": 0.0,
            "best_ticker": None,
            "worst_ticker": None,
        },
        "rows": [],
    }


def test_generate_weekly_review_uses_mocked_provider_only(tmp_path):
    db_path = tmp_path / "research.db"
    initialize_database(db_path)
    save_recommendations(
        db_path,
        trading_date="2025-01-03",
        strategy_version="v1",
        recommendations=[{"ticker": "AAPL", "score": 0.9, "rank": 1}],
    )

    provider = FakeMarketDataProvider(
        {
            "AAPL": [
                {"date": "2025-01-03", "close": 100.0},
                {"date": "2025-01-10", "close": 101.0},
            ],
            "SPY": [
                {"date": "2025-01-03", "close": 500.0},
                {"date": "2025-01-10", "close": 505.0},
            ],
        }
    )

    generate_weekly_review(
        db_path=db_path,
        start_date="2025-01-01",
        end_date="2025-01-10",
        benchmark_ticker="SPY",
        provider=provider,
    )

    assert provider.calls == [
        ("AAPL", "2025-01-03", "2025-01-10"),
        ("SPY", "2025-01-03", "2025-01-10"),
    ]


def test_generate_weekly_review_skips_same_day_recommendations(tmp_path):
    db_path = tmp_path / "research.db"
    initialize_database(db_path)
    save_recommendations(
        db_path,
        trading_date="2025-01-10",
        strategy_version="v1",
        recommendations=[{"ticker": "AAPL", "score": 0.9, "rank": 1}],
    )

    provider = FakeMarketDataProvider({})

    review = generate_weekly_review(
        db_path=db_path,
        start_date="2025-01-10",
        end_date="2025-01-10",
        benchmark_ticker="SPY",
        provider=provider,
    )

    assert review == {
        "summary": {
            "reviewed_count": 0,
            "win_count": 0,
            "loss_count": 0,
            "win_rate": 0.0,
            "average_return": 0.0,
            "average_benchmark_return": 0.0,
            "average_excess_return": 0.0,
            "best_ticker": None,
            "worst_ticker": None,
        },
        "rows": [],
    }


def test_generate_weekly_review_skips_recommendations_newer_than_default_horizon(tmp_path):
    db_path = tmp_path / "research.db"
    initialize_database(db_path)
    save_recommendations(
        db_path,
        trading_date="2025-01-08",
        strategy_version="v1",
        recommendations=[{"ticker": "AAPL", "score": 0.9, "rank": 1}],
    )

    provider = FakeMarketDataProvider({})

    review = generate_weekly_review(
        db_path=db_path,
        start_date="2025-01-01",
        end_date="2025-01-10",
        benchmark_ticker="SPY",
        provider=provider,
    )

    assert review == {
        "summary": {
            "reviewed_count": 0,
            "win_count": 0,
            "loss_count": 0,
            "win_rate": 0.0,
            "average_return": 0.0,
            "average_benchmark_return": 0.0,
            "average_excess_return": 0.0,
            "best_ticker": None,
            "worst_ticker": None,
        },
        "rows": [],
    }


def test_generate_weekly_review_reviews_mature_recommendations(tmp_path):
    db_path = tmp_path / "research.db"
    initialize_database(db_path)
    save_recommendations(
        db_path,
        trading_date="2025-01-03",
        strategy_version="v1",
        recommendations=[{"ticker": "AAPL", "score": 0.9, "rank": 1}],
    )

    provider = FakeMarketDataProvider(
        {
            "AAPL": [
                {"date": "2025-01-03", "close": 100.0},
                {"date": "2025-01-10", "close": 110.0},
            ],
            "SPY": [
                {"date": "2025-01-03", "close": 500.0},
                {"date": "2025-01-10", "close": 510.0},
            ],
        }
    )

    review = generate_weekly_review(
        db_path=db_path,
        start_date="2025-01-01",
        end_date="2025-01-10",
        benchmark_ticker="SPY",
        provider=provider,
    )

    assert review["summary"]["reviewed_count"] == 1
    assert review["rows"][0]["ticker"] == "AAPL"


def test_generate_weekly_review_does_not_call_provider_when_all_recommendations_are_immature(tmp_path):
    db_path = tmp_path / "research.db"
    initialize_database(db_path)
    save_recommendations(
        db_path,
        trading_date="2025-01-09",
        strategy_version="v1",
        recommendations=[{"ticker": "AAPL", "score": 0.9, "rank": 1}],
    )

    provider = FakeMarketDataProvider({})

    generate_weekly_review(
        db_path=db_path,
        start_date="2025-01-01",
        end_date="2025-01-10",
        benchmark_ticker="SPY",
        provider=provider,
    )

    assert provider.calls == []


def test_generate_weekly_review_skips_row_when_ticker_exit_price_is_missing(tmp_path):
    db_path = tmp_path / "research.db"
    initialize_database(db_path)
    save_recommendations(
        db_path,
        trading_date="2025-01-03",
        strategy_version="v1",
        recommendations=[{"ticker": "AAPL", "score": 0.9, "rank": 1}],
    )

    provider = FakeMarketDataProvider(
        {
            "AAPL": [
                {"date": "2025-01-03", "close": 100.0},
            ],
            "SPY": [
                {"date": "2025-01-03", "close": 500.0},
                {"date": "2025-01-10", "close": 510.0},
            ],
        }
    )

    review = generate_weekly_review(
        db_path=db_path,
        start_date="2025-01-01",
        end_date="2025-01-10",
        benchmark_ticker="SPY",
        provider=provider,
    )

    assert review == {
        "summary": {
            "reviewed_count": 0,
            "win_count": 0,
            "loss_count": 0,
            "win_rate": 0.0,
            "average_return": 0.0,
            "average_benchmark_return": 0.0,
            "average_excess_return": 0.0,
            "best_ticker": None,
            "worst_ticker": None,
        },
        "rows": [],
    }


def test_generate_weekly_review_skips_row_when_benchmark_exit_price_is_missing(tmp_path):
    db_path = tmp_path / "research.db"
    initialize_database(db_path)
    save_recommendations(
        db_path,
        trading_date="2025-01-03",
        strategy_version="v1",
        recommendations=[{"ticker": "AAPL", "score": 0.9, "rank": 1}],
    )

    provider = FakeMarketDataProvider(
        {
            "AAPL": [
                {"date": "2025-01-03", "close": 100.0},
                {"date": "2025-01-10", "close": 110.0},
            ],
            "SPY": [
                {"date": "2025-01-03", "close": 500.0},
            ],
        }
    )

    review = generate_weekly_review(
        db_path=db_path,
        start_date="2025-01-01",
        end_date="2025-01-10",
        benchmark_ticker="SPY",
        provider=provider,
    )

    assert review == {
        "summary": {
            "reviewed_count": 0,
            "win_count": 0,
            "loss_count": 0,
            "win_rate": 0.0,
            "average_return": 0.0,
            "average_benchmark_return": 0.0,
            "average_excess_return": 0.0,
            "best_ticker": None,
            "worst_ticker": None,
        },
        "rows": [],
    }


def test_weekly_review_script_exists_and_uses_default_benchmark(monkeypatch, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/generate_weekly_review.py"
    captured = {}

    def fake_generate_weekly_review(**kwargs):
        captured.update(kwargs)
        return {"summary": {}, "rows": []}

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.review.generate_weekly_review", fake_generate_weekly_review)

    runpy.run_path(str(script_path), run_name="__main__")

    assert captured == {
        "db_path": Path("data/stock_research.db"),
        "start_date": captured["start_date"],
        "end_date": captured["end_date"],
        "benchmark_ticker": "SPY",
    }


def test_weekly_review_script_handles_empty_review_result_gracefully(monkeypatch, capsys, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/generate_weekly_review.py"

    def fake_generate_weekly_review(**kwargs):
        return {
            "summary": {
                "reviewed_count": 0,
                "win_count": 0,
                "loss_count": 0,
                "win_rate": 0.0,
                "average_return": 0.0,
                "average_benchmark_return": 0.0,
                "average_excess_return": 0.0,
                "best_ticker": None,
                "worst_ticker": None,
            },
            "rows": [],
        }

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.review.generate_weekly_review", fake_generate_weekly_review)

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()

    assert "No recommendations ready for review." in captured.out


def test_weekly_review_script_prints_empty_state_when_no_mature_recommendations(monkeypatch, capsys, tmp_path):
    script_path = Path(__file__).resolve().parent.parent / "scripts/generate_weekly_review.py"

    def fake_generate_weekly_review(**kwargs):
        return {
            "summary": {
                "reviewed_count": 0,
                "win_count": 0,
                "loss_count": 0,
                "win_rate": 0.0,
                "average_return": 0.0,
                "average_benchmark_return": 0.0,
                "average_excess_return": 0.0,
                "best_ticker": None,
                "worst_ticker": None,
            },
            "rows": [],
        }

    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(Path.cwd()))
    monkeypatch.setattr("src.review.generate_weekly_review", fake_generate_weekly_review)

    runpy.run_path(str(script_path), run_name="__main__")
    captured = capsys.readouterr()

    assert "No recommendations ready for review." in captured.out


class FakeMarketDataProvider:
    def __init__(self, prices_by_ticker):
        self.prices_by_ticker = prices_by_ticker
        self.calls = []

    def fetch_daily_prices(self, ticker, start_date, end_date):
        self.calls.append((ticker, start_date, end_date))
        return self.prices_by_ticker[ticker]
