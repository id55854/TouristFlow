"""
Dynamic pricing engine — Section 6.2.

Constrained RevPAR maximization with seasonal elasticity curves.
"""

from __future__ import annotations

from typing import Any, Optional

from scipy.optimize import minimize_scalar


class PricingOptimizer:
    """Finds RevPAR-maximizing price per date × room type."""

    def __init__(self) -> None:
        self.elasticity_by_season = {
            "peak": -0.3,
            "high": -0.6,
            "shoulder": -1.0,
            "low": -1.5,
        }

        self.demand_multipliers = {
            "very_high": 1.40,
            "high": 1.15,
            "medium": 1.00,
            "low": 0.85,
            "very_low": 0.70,
        }

    def optimize_price(
        self,
        base_rate: float,
        forecasted_occupancy: float,
        season: str,
        demand_signals: list[dict],
        competitor_avg_rate: Optional[float],
        floor_rate: float,
        ceiling_rate: float,
        target_occupancy: float = 0.80,
    ) -> dict[str, Any]:
        elasticity = self.elasticity_by_season.get(season, -1.0)

        demand_score = self._aggregate_demand_signals(demand_signals)
        demand_level = self._classify_demand(demand_score)
        demand_multiplier = self.demand_multipliers[demand_level]

        adjusted_occupancy = min(0.98, forecasted_occupancy * demand_multiplier)

        def occupancy_at_price(price: float) -> float:
            if base_rate <= 0:
                return adjusted_occupancy
            ratio = price / base_rate
            occ = adjusted_occupancy * (ratio**elasticity)
            return max(0.0, min(0.98, occ))

        def neg_revpar(price: float) -> float:
            occ = occupancy_at_price(price)
            return -(occ * price)

        result = minimize_scalar(neg_revpar, bounds=(floor_rate, ceiling_rate), method="bounded")

        optimal_price = float(result.x)
        optimal_occupancy = occupancy_at_price(optimal_price)
        optimal_revpar = optimal_occupancy * optimal_price

        if optimal_occupancy < target_occupancy * 0.8:
            if adjusted_occupancy > 0 and elasticity != 0:
                required_ratio = (target_occupancy / adjusted_occupancy) ** (1 / elasticity)
                constrained_price = base_rate * required_ratio
                constrained_price = max(floor_rate, min(ceiling_rate, constrained_price))
                optimal_price = constrained_price
                optimal_occupancy = occupancy_at_price(optimal_price)
                optimal_revpar = optimal_occupancy * optimal_price

        if competitor_avg_rate and competitor_avg_rate > 0:
            position_ratio = optimal_price / competitor_avg_rate
            if position_ratio > 1.25:
                optimal_price = competitor_avg_rate * 1.20
            elif position_ratio < 0.75:
                optimal_price = competitor_avg_rate * 0.80
            optimal_occupancy = occupancy_at_price(optimal_price)
            optimal_revpar = optimal_occupancy * optimal_price

        optimal_price = round(optimal_price)

        current_occupancy = occupancy_at_price(base_rate)
        current_revpar = current_occupancy * base_rate

        change_pct = ((optimal_price - base_rate) / base_rate * 100) if base_rate > 0 else 0.0
        revpar_uplift = optimal_revpar - current_revpar

        rationale = self._generate_rationale(
            base_rate,
            optimal_price,
            change_pct,
            demand_level,
            season,
            demand_signals,
            competitor_avg_rate,
        )

        return {
            "recommended_rate": optimal_price,
            "current_rate": base_rate,
            "change_pct": round(change_pct, 1),
            "predicted_occupancy_current": round(current_occupancy, 3),
            "predicted_occupancy_recommended": round(optimal_occupancy, 3),
            "revpar_current": round(current_revpar, 2),
            "revpar_recommended": round(optimal_revpar, 2),
            "revpar_uplift": round(revpar_uplift, 2),
            "demand_level": demand_level,
            "elasticity_used": elasticity,
            "confidence": self._estimate_confidence(demand_signals, season),
            "rationale": rationale,
            "signals": demand_signals,
        }

    def run_whatif(
        self,
        base_rate: float,
        price_adjustment_pct: float,
        forecasted_occupancy: float,
        season: str,
        rooms_available: int,
        num_days: int = 1,
    ) -> dict[str, Any]:
        elasticity = self.elasticity_by_season.get(season, -1.0)
        new_rate = base_rate * (1 + price_adjustment_pct / 100)

        ratio = new_rate / base_rate if base_rate > 0 else 1
        new_occupancy = min(0.98, forecasted_occupancy * (ratio**elasticity))

        baseline_revenue = forecasted_occupancy * base_rate * rooms_available * num_days
        scenario_revenue = new_occupancy * new_rate * rooms_available * num_days

        return {
            "baseline": {
                "rate": base_rate,
                "occupancy": round(forecasted_occupancy, 3),
                "revpar": round(forecasted_occupancy * base_rate, 2),
                "total_revenue": round(baseline_revenue, 2),
                "rooms_sold": round(forecasted_occupancy * rooms_available * num_days),
            },
            "scenario": {
                "rate": round(new_rate, 2),
                "occupancy": round(new_occupancy, 3),
                "revpar": round(new_occupancy * new_rate, 2),
                "total_revenue": round(scenario_revenue, 2),
                "rooms_sold": round(new_occupancy * rooms_available * num_days),
            },
            "delta": {
                "revenue": round(scenario_revenue - baseline_revenue, 2),
                "revenue_pct": round(
                    (scenario_revenue - baseline_revenue) / baseline_revenue * 100 if baseline_revenue > 0 else 0,
                    1,
                ),
                "occupancy_pp": round((new_occupancy - forecasted_occupancy) * 100, 1),
                "rooms_delta": round((new_occupancy - forecasted_occupancy) * rooms_available * num_days),
            },
        }

    def _aggregate_demand_signals(self, signals: list[dict]) -> float:
        if not signals:
            return 50.0

        weighted_sum = 0.0
        total_weight = 0.0
        weights = {
            "event": 3.0,
            "flight": 2.0,
            "weather": 1.5,
            "trend": 1.0,
            "historical": 2.5,
            "competitor": 1.0,
        }

        for signal in signals:
            weight = weights.get(signal.get("type", ""), 1.0)
            magnitude = signal.get("magnitude", 50)
            if signal.get("impact") == "negative":
                magnitude = 100 - magnitude
            weighted_sum += magnitude * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 50.0

    def _classify_demand(self, score: float) -> str:
        if score >= 80:
            return "very_high"
        if score >= 65:
            return "high"
        if score >= 40:
            return "medium"
        if score >= 25:
            return "low"
        return "very_low"

    def _estimate_confidence(self, signals: list[dict], season: str) -> float:
        base_confidence = 0.70
        if signals:
            base_confidence += min(0.20, len(signals) * 0.04)
        if season in ("peak", "high"):
            base_confidence += 0.05
        return min(0.95, base_confidence)

    def _generate_rationale(
        self,
        current: float,
        recommended: float,
        change_pct: float,
        demand_level: str,
        season: str,
        signals: list[dict],
        comp_rate: Optional[float],
    ) -> str:
        direction = "increase" if change_pct > 0 else "decrease"
        parts: list[str] = []

        if abs(change_pct) < 1:
            parts.append(f"Maintain current rate of €{current:.0f}.")
        else:
            parts.append(f"Recommend {direction} to €{recommended:.0f} ({change_pct:+.1f}%).")

        parts.append(f"Demand is {demand_level.replace('_', ' ')} ({season} season).")

        for sig in signals[:2]:
            if sig.get("type") == "event":
                parts.append(f"Event impact: {sig.get('label', 'nearby event')}.")
            elif sig.get("type") == "weather":
                parts.append(f"Weather factor: {sig.get('label', 'favorable conditions')}.")
            elif sig.get("type") == "flight":
                parts.append(f"Flight data: {sig.get('label', 'arrivals trending up')}.")

        if comp_rate:
            position = "above" if recommended > comp_rate else "below"
            diff_pct = abs(recommended - comp_rate) / comp_rate * 100
            parts.append(f"Positioned {diff_pct:.0f}% {position} comp set (€{comp_rate:.0f}).")

        return " ".join(parts)


pricing_optimizer = PricingOptimizer()
