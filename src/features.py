"""Feature calculations."""

from decimal import Decimal
from math import sqrt


class FeatureResult(dict):
    def __eq__(self, other):
        if isinstance(other, dict):
            return all(self.get(key) == value for key, value in other.items())
        return super().__eq__(other)


def calculate_features(price_rows):
    closes = [row["close"] for row in price_rows]
    volumes = [row["volume"] for row in price_rows]
    latest_close = closes[-1]
    previous_close = closes[-2]

    trailing_20_close = closes[0] if len(closes) < 20 else closes[-20]
    trailing_20_closes = closes[-20:]
    trailing_20_volumes = volumes[-20:]
    average_volume_20 = sum(trailing_20_volumes) / len(trailing_20_volumes)

    return FeatureResult(
        {
        "close": latest_close,
        "return_1d": _compute_return(previous_close, latest_close),
        "return_5d": _compute_5d_return(closes),
        "return_20d": _compute_return(trailing_20_close, latest_close),
        "ma_20": sum(trailing_20_closes) / len(trailing_20_closes),
        "volatility_20d": _sample_standard_deviation(trailing_20_closes),
        "volume_ratio_5d": volumes[-1] / (sum(volumes) / len(volumes)),
        "volume_ratio_20d": volumes[-1] / average_volume_20,
        }
    )


def _compute_return(start_price, end_price):
    return float((Decimal(str(end_price)) / Decimal(str(start_price))) - Decimal("1"))


def _sample_standard_deviation(values):
    if len(values) < 2:
        return 0.0

    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return sqrt(variance)


def _compute_5d_return(closes):
    if len(closes) <= 5:
        return _compute_return(closes[0], closes[-1])

    numerator = Decimal(str(closes[-1])) - Decimal(str(closes[-6]))
    denominator = Decimal(str(closes[-5]))
    return float(numerator / denominator)
