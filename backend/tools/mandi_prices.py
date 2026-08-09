"""
mandi_prices.py — Tool: fetch and surface current mandi prices.

Wraps the data_gov service with clear structured results so Gemma can
decide what to do when local data is unavailable.
"""

from __future__ import annotations

from typing import Any

from backend.services.data_gov import fetch_mandi_prices as _fetch
from backend.agent.schemas import MandiRecord


def get_mandi_prices(
    state: str,
    commodity: str,
    district: str | None = None,
    market: str | None = None,
    variety: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """
    Retrieve current government mandi prices.

    If district + commodity yields no data, returns status="no_results"
    so Gemma can decide to expand the search to a broader state-level query.

    Args:
        state:     Indian state name (e.g. "Uttar Pradesh")
        commodity: Crop/commodity name (e.g. "Wheat", "Potato")
        district:  Optional district filter (e.g. "Prayagraj")
        market:    Optional specific market name
        variety:   Optional variety filter
        limit:     Max records to return

    Returns:
        {
            "status": "ok" | "no_results" | "error",
            "total": int,
            "records": list[dict],   # serialized MandiRecord objects
            "message": str,
        }
    """
    result = _fetch(
        state=state,
        district=district,
        commodity=commodity,
        market=market,
        variety=variety,
        limit=limit,
    )

    # Serialize MandiRecord objects to plain dicts for JSON transport
    if result["status"] == "ok":
        result["records"] = [
            r.model_dump() if isinstance(r, MandiRecord) else r
            for r in result["records"]
        ]

    return result
