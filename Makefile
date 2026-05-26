test:
	./.venv/bin/python -m pytest -q

reset:
	./.venv/bin/python scripts/reset_database.py

daily:
	./.venv/bin/python scripts/generate_daily_recommendations.py

list:
	./.venv/bin/python scripts/list_recommendations.py

weekly:
	./.venv/bin/python scripts/generate_weekly_review.py

backtest:
	./.venv/bin/python scripts/backtest_strategy.py \
		--tickers AAPL MSFT NVDA \
		--benchmark SPY \
		--start-date 2026-02-24 \
		--end-date 2026-05-25 \
		--holding-days 5 \
		--top-n 2 \
		--summary-only

smoke:
	./.venv/bin/python scripts/smoke_yfinance.py
