"""
transport.py — Tool: estimate transport cost based on configurable rate.

IMPORTANT: This is a prototype estimate, NOT an official government rate.
The UI must display: "Transport cost is an estimate based on the configured
prototype rate and may differ from actual local costs."
"""

from backend.config import settings


def estimate_transport_cost(
    distance_km: float,
    quantity_quintals: float,
    rate_per_quintal_km: float | None = None,
) -> dict:
    """
    Estimate transportation cost for moving produce to a mandi.

    Args:
        distance_km:          Approximate distance to market in km.
        quantity_quintals:    Quantity of produce in quintals.
        rate_per_quintal_km:  Rate in ₹ per quintal per km.
                              Defaults to TRANSPORT_RATE_PER_QUINTAL_KM from config.

    Returns:
        dict with keys:
            distance_km, quantity_quintals, rate_per_quintal_km,
            estimated_transport_cost
    """
    rate = rate_per_quintal_km if rate_per_quintal_km is not None else settings.transport_rate_per_quintal_km

    cost = round(distance_km * quantity_quintals * rate, 2)

    return {
        "distance_km": distance_km,
        "quantity_quintals": quantity_quintals,
        "rate_per_quintal_km": rate,
        "estimated_transport_cost": cost,
        "note": (
            "Transport cost is an estimate based on a prototype assumption "
            "and may differ from actual local costs."
        ),
    }
