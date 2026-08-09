"""
pipeline.py — Market comparison and ranking pipeline.

Orchestrates the full deterministic flow:
  1. Fetch current mandi prices (with state-wide fallback)
  2. Resolve market coordinates
  3. Filter by distance radius
  4. Estimate transport cost
  5. Calculate gross value + estimated net return
  6. Rank by estimated net return (descending)

Gemma uses the output of this pipeline to reason and explain —
it does NOT perform any of these calculations itself.
"""

from __future__ import annotations

import logging
from typing import Optional

from backend.config import settings
from backend.agent.schemas import MarketCandidate
from backend.tools.mandi_prices import get_mandi_prices
from backend.tools.market_locations import (
    get_origin_coordinates,
    find_nearby_markets,
)
from backend.tools.transport import estimate_transport_cost
from backend.tools.returns import calculate_estimated_return

logger = logging.getLogger(__name__)


def rank_market_options(
    origin: str,
    state: str,
    commodity: str,
    quantity_quintals: float,
    search_radius_km: Optional[float] = None,
    district: Optional[str] = None,
) -> dict:
    """
    Full market comparison pipeline.

    Args:
        origin:            Farmer's city/district name (e.g. "Prayagraj").
        state:             State to search (e.g. "Uttar Pradesh").
        commodity:         Crop name (e.g. "Wheat").
        quantity_quintals: Quantity to sell.
        search_radius_km:  Max distance to consider. Defaults to config value.
        district:          Optional district for initial local search.

    Returns:
        {
            "status": "ok" | "no_results" | "error",
            "origin": str,
            "origin_coordinates": {"lat": float, "lon": float} | None,
            "commodity": str,
            "quantity_quintals": float,
            "search_radius_km": float,
            "local_search_attempted": bool,
            "local_records_found": int,
            "state_wide_fallback_used": bool,
            "total_api_records": int,
            "candidates_in_radius": int,
            "ranked_markets": list[dict],
            "top_recommendation": dict | None,
            "message": str,
        }
    """
    radius = search_radius_km or settings.default_search_radius_km

    # -- Step 1: Resolve origin coordinates --
    coords = get_origin_coordinates(origin)
    if coords is None:
        return {
            "status": "error",
            "origin": origin,
            "origin_coordinates": None,
            "commodity": commodity,
            "quantity_quintals": quantity_quintals,
            "search_radius_km": radius,
            "local_search_attempted": False,
            "local_records_found": 0,
            "state_wide_fallback_used": False,
            "total_api_records": 0,
            "candidates_in_radius": 0,
            "ranked_markets": [],
            "top_recommendation": None,
            "message": (
                f"Could not determine coordinates for '{origin}'. "
                "Please enter a known district or city name."
            ),
        }

    origin_lat, origin_lon = coords
    local_search_attempted = False
    local_records_found = 0
    state_wide_fallback = False

    # -- Step 2: Try local district search first --
    search_district = district or origin
    local_search_attempted = True

    price_result = get_mandi_prices(
        state=state,
        commodity=commodity,
        district=search_district,
        limit=100,
    )
    local_records_found = price_result.get("total", 0)

    # -- Step 3: Fallback to state-wide if no local results --
    if price_result["status"] != "ok" or local_records_found == 0:
        logger.info(
            "No local results for %s in %s — expanding to state-wide search.",
            commodity, search_district,
        )
        state_wide_fallback = True
        price_result = get_mandi_prices(
            state=state,
            commodity=commodity,
            limit=200,
        )

    if price_result["status"] == "error":
        return {
            "status": "error",
            "origin": origin,
            "origin_coordinates": {"lat": origin_lat, "lon": origin_lon},
            "commodity": commodity,
            "quantity_quintals": quantity_quintals,
            "search_radius_km": radius,
            "local_search_attempted": local_search_attempted,
            "local_records_found": local_records_found,
            "state_wide_fallback_used": state_wide_fallback,
            "total_api_records": 0,
            "candidates_in_radius": 0,
            "ranked_markets": [],
            "top_recommendation": None,
            "message": price_result["message"],
        }

    if price_result["status"] == "no_results":
        return {
            "status": "no_results",
            "origin": origin,
            "origin_coordinates": {"lat": origin_lat, "lon": origin_lon},
            "commodity": commodity,
            "quantity_quintals": quantity_quintals,
            "search_radius_km": radius,
            "local_search_attempted": local_search_attempted,
            "local_records_found": local_records_found,
            "state_wide_fallback_used": state_wide_fallback,
            "total_api_records": 0,
            "candidates_in_radius": 0,
            "ranked_markets": [],
            "top_recommendation": None,
            "message": (
                f"No current mandi records found for {commodity} in {state}. "
                "The commodity may not be listed in today's feed."
            ),
        }

    raw_records = price_result["records"]
    total_api_records = price_result["total"]

    # -- Step 4: Filter by distance --
    nearby = find_nearby_markets(origin_lat, origin_lon, raw_records, max_distance_km=radius)
    located = [m for m in nearby if m.location_available]

    if not located:
        return {
            "status": "no_results",
            "origin": origin,
            "origin_coordinates": {"lat": origin_lat, "lon": origin_lon},
            "commodity": commodity,
            "quantity_quintals": quantity_quintals,
            "search_radius_km": radius,
            "local_search_attempted": local_search_attempted,
            "local_records_found": local_records_found,
            "state_wide_fallback_used": state_wide_fallback,
            "total_api_records": total_api_records,
            "candidates_in_radius": 0,
            "ranked_markets": [],
            "top_recommendation": None,
            "message": (
                f"No suitable market found for {commodity} within {radius:.0f} km of {origin}. "
                "Try increasing the search radius."
            ),
        }

    # -- Step 5 & 6: Transport + net return for each candidate --
    for candidate in located:
        transport = estimate_transport_cost(
            distance_km=candidate.distance_km,
            quantity_quintals=quantity_quintals,
        )
        returns = calculate_estimated_return(
            quantity_quintals=quantity_quintals,
            modal_price=candidate.modal_price,
            estimated_transport_cost=transport["estimated_transport_cost"],
        )
        candidate.estimated_transport_cost = transport["estimated_transport_cost"]
        candidate.gross_value              = returns["gross_value"]
        candidate.estimated_net_return     = returns["estimated_net_return"]

    # -- Step 7: Rank by estimated net return (descending) --
    ranked = sorted(located, key=lambda c: c.estimated_net_return or 0, reverse=True)

    top = ranked[0] if ranked else None

    return {
        "status": "ok",
        "origin": origin,
        "origin_coordinates": {"lat": origin_lat, "lon": origin_lon},
        "commodity": commodity,
        "quantity_quintals": quantity_quintals,
        "search_radius_km": radius,
        "local_search_attempted": local_search_attempted,
        "local_records_found": local_records_found,
        "state_wide_fallback_used": state_wide_fallback,
        "total_api_records": total_api_records,
        "candidates_in_radius": len(ranked),
        "ranked_markets": [c.model_dump() for c in ranked[:10]],
        "top_recommendation": top.model_dump() if top else None,
        "message": (
            f"Found {len(ranked)} market(s) within {radius:.0f} km of {origin} "
            f"with current {commodity} prices."
            + (" (State-wide search used — no local listings found.)" if state_wide_fallback else "")
        ),
        "transport_note": (
            "Transport cost is an estimate based on a prototype assumption "
            f"of ₹{settings.transport_rate_per_quintal_km}/quintal/km "
            "and may differ from actual local costs."
        ),
    }
