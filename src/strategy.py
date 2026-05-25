"""Explainable strategy scoring."""


class WeightedStrategy:
    def __init__(self, version, weights):
        self.version = version
        self.weights = weights

    def score(self, symbol, features):
        component_scores = {}

        for feature_name, weight in self.weights.items():
            feature_value = features[feature_name]
            contribution = feature_value * weight
            component_scores[feature_name] = contribution

        total_score = sum(component_scores.values())

        return {
            "symbol": symbol,
            "strategy_version": self.version,
            "score": total_score,
            "component_scores": component_scores,
        }
