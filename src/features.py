"""Feature calculations."""

from decimal import Decimal
from math import sqrt


def calculate_features(price_rows):
    closes = [row["close"] for row in price_rows]
    volumes = [row["volume"] for row in price_rows]
    latest_close = closes[-1]
    previous_close = closes[-2]

    trailing_5_close = closes[0] if len(closes) < 5 else closes[-5]

    return {
        "close": latest_close,
        "return_1d": _compute_return(previous_close, latest_close),
        "return_5d": _compute_return(trailing_5_close, latest_close),
        "volume_ratio_5d": volumes[-1] / (sum(volumes) / len(volumes)),
    }


def _compute_return(start_price, end_price):
    return float((Decimal(str(end_price)) / Decimal(str(start_price))) - Decimal("1"))


def _sample_standard_deviation(values):
    if len(values) < 2:
        return 0.0

    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return sqrt(variance)
