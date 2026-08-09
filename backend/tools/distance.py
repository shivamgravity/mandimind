"""
distance.py — Tool: deterministic Haversine distance calculation.

NOTE: This is approximate straight-line (geographic) distance.
      It is NOT driving distance.
      The UI must clearly state "Approximate geographic distance."
"""

import math


def haversine_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate the straight-line distance between two GPS coordinates
    using the Haversine formula.

    Returns distance in kilometres.
    """
    R = 6371.0  # Earth radius in km

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(R * c, 2)
