"""Generate a local HTML report for research outputs."""

import argparse
from datetime import datetime, date, timedelta
from html import escape
from pathlib import Path
import sqlite3
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.backtest import run_backtest
from src.config import DEFAULT_DB_PATH, load_config
from src.review import generate_weekly_review


COMPARISON_FIELDS = [
    "config",
    "strategy_version",
    "tested_count",
    "win_count",
    "loss_count",
    "win_rate",
    "average_return",
    "average_benchmark_return",
    "average_excess_return",
    "median_return",
    "median_excess_return",
    "best_ticker",
    "worst_ticker",
    "best_return",
    "worst_return",
]


def main(argv=None):
    args = _parse_args(argv)
    config = load_config(args.config)
    output_path = Path(args.output)
    db_path = Path(args.db if args.db is not None else config["database_path"])
    strategy_config_paths = args.strategy_configs or [args.config]

    recommendations = _read_recommendations(db_path)
    weekly_review = _build_weekly_review(config, db_path)
    backtest = _build_backtest(config)
    strategy_rows = _build_strategy_comparison(strategy_config_paths)

    html = _render_report(
        generated_at=datetime.now().isoformat(sep=" ", timespec="seconds"),
        recommendations=recommendations,
        weekly_review=weekly_review,
        backtest=backtest,
        strategy_rows=strategy_rows,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html)
    print(f"Wrote report: {output_path}")
    return 0


def _parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/report.html")
    parser.add_argument("--db")
    parser.add_argument("--config", default="config/default.json")
    parser.add_argument("--strategy-configs", nargs="+")
    return parser.parse_known_args(argv)[0]


def _read_recommendations(db_path):
    connection = sqlite3.connect(db_path)
    try:
        rows = connection.execute(
            """
            SELECT trading_date, rank, symbol, score, entry_price, strategy_version
            FROM recommendations
            ORDER BY trading_date DESC, rank ASC, symbol ASC
            LIMIT 20
            """
        ).fetchall()
    finally:
        connection.close()

    return [
        {
            "trading_date": row[0],
            "rank": row[1],
            "symbol": row[2],
            "score": row[3],
            "entry_price": row[4],
            "strategy_version": row[5],
        }
        for row in rows
    ]


def _build_weekly_review(config, db_path):
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    return generate_weekly_review(
        db_path=db_path,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        benchmark_ticker=config["benchmark"],
        review_horizon_days=config["review_horizon_days"],
    )


def _build_backtest(config):
    return run_backtest(
        tickers=config["tickers"],
        benchmark_ticker=config["benchmark"],
        start_date=_resolve_backtest_start(config),
        end_date=_resolve_backtest_end(config),
        holding_days=config["holding_days"],
        top_n=config["top_n"],
        strategy_version=config["strategy"]["version"],
        strategy_weights=config["strategy"]["weights"],
    )


def _build_strategy_comparison(config_paths):
    rows = []
    for config_path_text in config_paths:
        config = load_config(config_path_text)
        result = run_backtest(
            tickers=config["tickers"],
            benchmark_ticker=config["benchmark"],
            start_date=_resolve_backtest_start(config),
            end_date=_resolve_backtest_end(config),
            holding_days=config["holding_days"],
            top_n=config["top_n"],
            strategy_version=config["strategy"]["version"],
            strategy_weights=config["strategy"]["weights"],
        )
        row = {
            "config": str(config_path_text),
            "strategy_version": config["strategy"]["version"],
            **result["summary"],
        }
        rows.append({field: row.get(field) for field in COMPARISON_FIELDS})
    return rows


def _resolve_backtest_start(config):
    if config.get("backtest_start_date") is not None:
        return config["backtest_start_date"]
    return (date.today() - timedelta(days=config["lookback_days"])).isoformat()


def _resolve_backtest_end(config):
    if config.get("backtest_end_date") is not None:
        return config["backtest_end_date"]
    return date.today().isoformat()


def _render_report(generated_at, recommendations, weekly_review, backtest, strategy_rows):
    sections = [
        "<!doctype html>",
        "<html>",
        "<head>",
        '<meta charset="utf-8">',
        "<title>Stock Signal Research Report</title>",
        "<style>",
        "body { font-family: Arial, sans-serif; margin: 2rem; color: #222; }",
        "h1, h2 { margin-bottom: 0.5rem; }",
        "section { margin-bottom: 2rem; }",
        "table { border-collapse: collapse; width: 100%; margin-top: 0.5rem; }",
        "th, td { border: 1px solid #ccc; padding: 0.4rem; text-align: left; }",
        "th { background: #f3f3f3; }",
        "p.meta { color: #555; }",
        "</style>",
        "</head>",
        "<body>",
        "<h1>Stock Signal Research Report</h1>",
        f'<p class="meta">Generated: {escape(generated_at)}</p>',
        _render_recommendations_section(recommendations),
        _render_weekly_review_section(weekly_review),
        _render_backtest_section(backtest),
        _render_strategy_section(strategy_rows),
        "</body>",
        "</html>",
    ]
    return "\n".join(sections)


def _render_recommendations_section(rows):
    if not rows:
        body = "<p>No recommendations found.</p>"
    else:
        body = (
            f"<p>Saved recommendations: {len(rows)}</p>"
            + _render_table(
                rows,
                ["trading_date", "rank", "symbol", "score", "entry_price", "strategy_version"],
            )
        )
    return f"<section><h2>Saved Recommendations Summary</h2>{body}</section>"


def _render_weekly_review_section(review):
    summary = review["summary"]
    if summary.get("reviewed_count", 0) == 0:
        body = "<p>No recommendations ready for review.</p>"
    else:
        body = _render_key_value_list(
            [
                ("reviewed_count", summary.get("reviewed_count")),
                ("win_count", summary.get("win_count")),
                ("loss_count", summary.get("loss_count")),
                ("win_rate", summary.get("win_rate")),
                ("average_return", summary.get("average_return")),
                ("average_benchmark_return", summary.get("average_benchmark_return")),
                ("average_excess_return", summary.get("average_excess_return")),
                ("best_ticker", summary.get("best_ticker")),
                ("worst_ticker", summary.get("worst_ticker")),
            ]
        )
    return f"<section><h2>Weekly Review Summary</h2>{body}</section>"


def _render_backtest_section(backtest):
    summary = backtest["summary"]
    if not backtest["rows"]:
        body = "<p>No backtest rows available.</p>"
    else:
        body = _render_key_value_list(
            [
                ("tested_count", summary.get("tested_count")),
                ("win_count", summary.get("win_count")),
                ("loss_count", summary.get("loss_count")),
                ("win_rate", summary.get("win_rate")),
                ("average_return", summary.get("average_return")),
                ("average_benchmark_return", summary.get("average_benchmark_return")),
                ("average_excess_return", summary.get("average_excess_return")),
                ("median_return", summary.get("median_return")),
                ("median_excess_return", summary.get("median_excess_return")),
                ("best_ticker", summary.get("best_ticker")),
                ("worst_ticker", summary.get("worst_ticker")),
                ("best_return", summary.get("best_return")),
                ("worst_return", summary.get("worst_return")),
            ]
        )
    return f"<section><h2>Backtest Summary</h2>{body}</section>"


def _render_strategy_section(rows):
    if not rows or all(row.get("tested_count", 0) == 0 for row in rows):
        body = "<p>No strategy results to display.</p>"
    else:
        body = _render_table(rows, COMPARISON_FIELDS)
    return f"<section><h2>Strategy Comparison Summary</h2>{body}</section>"


def _render_table(rows, fields):
    header = "".join(f"<th>{escape(field)}</th>" for field in fields)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{escape(str(row.get(field)))}</td>" for field in fields)
        body_rows.append(f"<tr>{cells}</tr>")
    return "<table><thead><tr>" + header + "</tr></thead><tbody>" + "".join(body_rows) + "</tbody></table>"


def _render_key_value_list(items):
    return "<ul>" + "".join(
        f"<li><strong>{escape(str(key))}</strong>: {escape(str(value))}</li>"
        for key, value in items
    ) + "</ul>"


if __name__ == "__main__":
    main()
