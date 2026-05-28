"""Generate and persist daily stock recommendations."""

import argparse
from datetime import date, timedelta
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.recommendations import build_recommendation_summary, generate_daily_recommendations


def main(argv=None):
    args = _parse_args(argv)
    config = load_config(args.config)
    lookback_days = args.lookback_days
    if lookback_days is None:
        lookback_days = config["lookback_days"]
    end_date = date.today()
    start_date = end_date - timedelta(days=lookback_days)
    db_path = Path(args.db if args.db is not None else config["database_path"])
    tickers = _normalize_tickers(args.tickers) if args.tickers is not None else config["tickers"]
    benchmark = args.benchmark if args.benchmark is not None else config["benchmark"]

    recommendations = generate_daily_recommendations(
        tickers=tickers,
        benchmark_ticker=benchmark,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        db_path=db_path,
        strategy_version=config["strategy"]["version"],
        strategy_weights=config["strategy"]["weights"],
    )

    if recommendations:
        summary = build_recommendation_summary(recommendations)
        print(f"Today: {summary['market_signal_summary']}")
        print(summary["best_candidate_summary"])
        print(summary["risk_summary"])
        print()

    for recommendation in recommendations:
        print(f"rank={recommendation['rank']}")
        print(f"ticker={recommendation['ticker']}")
        print(f"score={recommendation['score']}")
        print(f"signal_strength={recommendation['signal_strength']}")
        print(f"entry_price={recommendation['entry_price']}")
        print(f"strategy_version={recommendation['strategy_version']}")
        print(f"reasons={recommendation['reasons']}")
        print(f"risk_notes={recommendation['risk_notes']}")
        print()

    if recommendations and all(recommendation["score"] <= 0 for recommendation in recommendations):
        print(
            "Warning: all recommendation scores are negative. This means there is no strong buy signal today."
        )

    return 0


def _parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--config")
    parser.add_argument("--db")
    parser.add_argument("--tickers", nargs="+")
    parser.add_argument("--benchmark")
    parser.add_argument("--lookback-days", type=int)
    return parser.parse_known_args(argv)[0]


def _normalize_tickers(raw_tickers):
    if len(raw_tickers) == 1 and "," in raw_tickers[0]:
        return [ticker.strip() for ticker in raw_tickers[0].split(",") if ticker.strip()]
    return raw_tickers


if __name__ == "__main__":
    main()
