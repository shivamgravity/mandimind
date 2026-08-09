"""
market_locations.py — Tool: market GPS coordinate lookup and nearby-market filtering.

Data source: data/market_locations.csv
The CSV covers UP mandis needed for the hackathon demo.
The Government API remains the source of truth for current prices.
"""

from __future__ import annotations

import csv
import logging
import os
from functools import lru_cache
from typing import Optional

from backend.agent.schemas import MarketLocation, MarketCandidate
from backend.tools.distance import haversine_distance

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CSV path — relative to project root
# ---------------------------------------------------------------------------

_CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "market_locations.csv"
)

# ---------------------------------------------------------------------------
# Known origin cities (for MVP — user types a city name)
# ---------------------------------------------------------------------------

_ORIGIN_CITIES: dict[str, tuple[float, float]] = {
    # Uttar Pradesh
    "prayagraj":    (25.4358, 81.8463),
    "allahabad":    (25.4358, 81.8463),
    "lucknow":      (26.8467, 80.9462),
    "kanpur":       (26.4499, 80.3319),
    "varanasi":     (25.3176, 82.9739),
    "agra":         (27.1767, 78.0081),
    "mathura":      (27.4924, 77.6737),
    "meerut":       (28.9845, 77.7064),
    "bareilly":     (28.3670, 79.4304),
    "aligarh":      (27.8974, 78.0880),
    "gorakhpur":    (26.7606, 83.3732),
    "moradabad":    (28.8386, 78.7733),
    "saharanpur":   (29.9640, 77.5460),
    "faizabad":     (26.7752, 82.1456),
    "ayodhya":      (26.7947, 82.1979),
    "jhansi":       (25.4484, 78.5685),
    "ghaziabad":    (28.6692, 77.4538),
    "noida":        (28.5355, 77.3910),
    "raebareli":    (26.2341, 81.2343),
    "sultanpur":    (26.2637, 82.0724),
    "pratapgarh":   (25.8933, 81.9943),
    "fatehpur":     (25.9300, 80.8100),
    "banda":        (25.4747, 80.3358),
    "chitrakoot":   (25.1932, 80.8534),
    "mirzapur":     (25.1449, 82.5685),
    "jaunpur":      (25.7463, 82.6836),
    "gonda":        (27.1314, 81.9593),
    "sitapur":      (27.5620, 80.6824),
    "hardoi":       (27.3960, 80.1300),
    "unnao":        (26.5470, 80.4938),
    "etawah":       (26.7746, 79.0231),
    "mainpuri":     (27.2316, 79.0188),
    "farrukhabad":  (27.3919, 79.5786),
    "kannauj":      (27.0577, 79.9102),
    "auraiya":      (26.4667, 79.5167),
    "jalaun":       (26.1368, 79.3358),
    "orai":         (25.9791, 79.4529),
    "hamirpur":     (25.9534, 80.1451),
    "mahoba":       (25.2925, 79.8723),
    "lalitpur":     (24.6889, 78.4120),
    "lakhimpur":    (27.9470, 80.7813),
    "kheri":        (27.9470, 80.7813),
    "mau":          (25.9414, 83.5616),
    "ballia":       (25.7615, 84.1482),
    "azamgarh":     (26.0688, 83.1848),
    "bulandshahr":  (28.4070, 77.8499),
    "firozabad":    (27.1521, 78.3942),
    "hathras":      (27.5973, 78.0528),
    "etah":         (27.5594, 78.6637),
    "kasganj":      (27.8093, 78.6464),
    "sambhal":      (28.5800, 78.5700),
}


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_locations() -> list[dict]:
    """Load and cache the market locations CSV."""
    path = os.path.normpath(_CSV_PATH)
    rows = []
    try:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    rows.append({
                        "market":    row["market"].strip(),
                        "district":  row["district"].strip(),
                        "state":     row["state"].strip(),
                        "latitude":  float(row["latitude"]),
                        "longitude": float(row["longitude"]),
                        "source":    row.get("source", "").strip(),
                    })
                except (ValueError, KeyError) as exc:
                    logger.warning("Skipping bad CSV row %s: %s", row, exc)
    except FileNotFoundError:
        logger.error("market_locations.csv not found at %s", path)
    return rows


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def get_market_location(
    market: str,
    district: str | None = None,
    state: str | None = None,
) -> Optional[MarketLocation]:
    """
    Look up GPS coordinates for a named market.

    Matching strategy (in order):
      1. Exact market name + district + state
      2. Exact market name + state
      3. Exact market name only
      4. Case-insensitive partial match on market name

    Returns None if no match found.
    """
    rows = _load_locations()
    market_lower = market.lower().strip()

    # Try progressively looser matches
    candidates = []
    for row in rows:
        row_market = row["market"].lower()
        name_match = row_market == market_lower or market_lower in row_market or row_market in market_lower
        if not name_match:
            continue

        score = 0
        if state and row["state"].lower() == state.lower():
            score += 2
        if district and row["district"].lower() == district.lower():
            score += 3
        candidates.append((score, row))

    if not candidates:
        logger.info("No location found for market=%r district=%r state=%r", market, district, state)
        return None

    # Pick best match
    best = max(candidates, key=lambda x: x[0])[1]
    return MarketLocation(
        market=best["market"],
        district=best["district"],
        state=best["state"],
        latitude=best["latitude"],
        longitude=best["longitude"],
        source=best["source"],
    )


def get_origin_coordinates(location_name: str) -> Optional[tuple[float, float]]:
    """
    Resolve a user-supplied city/district name to (latitude, longitude).

    Checks:
      1. Known origin cities lookup (case-insensitive)
      2. Market locations CSV (treats it as a market city)

    Returns None if the location cannot be resolved.
    """
    key = location_name.lower().strip()

    # Direct lookup
    if key in _ORIGIN_CITIES:
        return _ORIGIN_CITIES[key]

    # Partial match (e.g. "Prayagraj" matches "prayagraj apmc")
    for city_key, coords in _ORIGIN_CITIES.items():
        if key in city_key or city_key in key:
            return coords

    # Fall back to CSV
    loc = get_market_location(location_name)
    if loc:
        return (loc.latitude, loc.longitude)

    logger.warning("Could not resolve origin location: %r", location_name)
    return None


def find_nearby_markets(
    origin_lat: float,
    origin_lon: float,
    candidate_markets: list[dict],
    max_distance_km: float = 150.0,
) -> list[MarketCandidate]:
    """
    Filter a list of mandi price records to those within max_distance_km
    of the origin, annotating each with distance and location data.

    Args:
        origin_lat:         Farmer's latitude.
        origin_lon:         Farmer's longitude.
        candidate_markets:  List of MandiRecord dicts from get_mandi_prices().
        max_distance_km:    Maximum radius to consider.

    Returns:
        List of MarketCandidate objects sorted by distance (closest first).
        Markets with unknown coordinates are included with location_available=False.
    """
    results: list[MarketCandidate] = []

    for rec in candidate_markets:
        market_name = rec.get("market", "")
        district    = rec.get("district", "")
        state       = rec.get("state", "")

        loc = get_market_location(market_name, district, state)

        candidate = MarketCandidate(
            market=market_name,
            district=district,
            state=state,
            modal_price=rec.get("modal_price", 0),
            min_price=rec.get("min_price", 0),
            max_price=rec.get("max_price", 0),
            variety=rec.get("variety", ""),
            arrival_date=rec.get("arrival_date", ""),
        )

        if loc is None:
            candidate.location_available = False
            # Still include but mark unavailable — don't silently drop
            results.append(candidate)
            continue

        dist = haversine_distance(origin_lat, origin_lon, loc.latitude, loc.longitude)

        if dist > max_distance_km:
            continue  # Outside radius

        candidate.latitude             = loc.latitude
        candidate.longitude            = loc.longitude
        candidate.distance_km          = dist
        candidate.location_available   = True
        results.append(candidate)

    # Sort: located markets by distance first, then unlocated at the end
    results.sort(key=lambda c: (not c.location_available, c.distance_km or 9999))
    return results
