"""Generate and persist daily stock recommendations."""

from datetime import date, timedelta
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.recommendations import generate_daily_recommendations


DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "SPY"]
DEFAULT_BENCHMARK = "SPY"
DEFAULT_DB_PATH = Path("data/stock_research.db")


def main():
    end_date = date.today()
    start_date = end_date - timedelta(days=90)

    recommendations = generate_daily_recommendations(
        tickers=DEFAULT_TICKERS,
        benchmark_ticker=DEFAULT_BENCHMARK,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        db_path=DEFAULT_DB_PATH,
    )

    for recommendation in recommendations:
        print(f"rank={recommendation['rank']}")
        print(f"ticker={recommendation['ticker']}")
        print(f"score={recommendation['score']}")
        print(f"entry_price={recommendation['entry_price']}")
        print(f"strategy_version={recommendation['strategy_version']}")
        print(f"reasons={recommendation['reasons']}")
        print(f"risk_notes={recommendation['risk_notes']}")
        print()

    return 0


if __name__ == "__main__":
    main()
