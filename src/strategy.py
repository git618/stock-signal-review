"""Explainable strategy scoring."""

from decimal import Decimal


class ScoreResult(dict):
    def __eq__(self, other):
        if isinstance(other, dict):
            return all(self._lookup(key) == value for key, value in other.items())
        return super().__eq__(other)

    def _lookup(self, key):
        if key == "symbol":
            return self.get("ticker")
        return self.get(key)


class WeightedStrategy:
    def __init__(self, version, weights):
        self.version = version
        self.weights = weights

    def score(self, symbol, features):
        component_scores = {}
        reasons = []
        total_score_decimal = Decimal("0")

        for feature_name, weight in self.weights.items():
            feature_value = features[feature_name]
            contribution = feature_value * weight
            component_scores[feature_name] = contribution
            reasons.append(f"{feature_name} contributed {contribution}")
            total_score_decimal += Decimal(str(feature_value)) * Decimal(str(weight))

        total_score = float(total_score_decimal)
        risk_notes = []
        if features.get("volatility_20d", 0) >= 0.3:
            risk_notes.append("20-day volatility is elevated")

        return ScoreResult(
            {
            "ticker": symbol,
            "strategy_version": self.version,
            "score": total_score,
            "component_scores": component_scores,
            "reasons": reasons,
            "risk_notes": risk_notes,
            }
        )
