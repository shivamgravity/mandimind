"""
data_gov.py — API client for the Government of India Open Data mandi-price feed.

Dataset: Current Daily Price of Various Commodities from Various Markets (Mandi)
Source:  Ministry of Agriculture and Farmers Welfare
URL:     https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070

Uses `requests` (system SSL store, curl-equivalent behaviour).

Error handling covers:
  - timeout
  - HTTP errors (403 invalid key, 429 rate limit, 5xx server errors)
  - empty results
  - malformed response
"""

from __future__ import annotations

import logging
from typing import Any

import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError, RequestException

from backend.config import settings
from backend.agent.schemas import MandiRecord

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_BASE_URL = settings.data_gov_base_url
_TIMEOUT_SECONDS = 20

# data.gov.in blocks Python default User-Agents — must mimic curl
_HEADERS = {"User-Agent": "curl/8.5.0"}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize_record(raw: dict[str, Any]) -> MandiRecord | None:
    """
    Convert a raw data.gov.in JSON record into a MandiRecord.
    Returns None if the record is malformed or missing required fields.
    """
    try:
        return MandiRecord(
            state=str(raw.get("state", "")).strip(),
            district=str(raw.get("district", "")).strip(),
            market=str(raw.get("market", "")).strip(),
            commodity=str(raw.get("commodity", "")).strip(),
            variety=str(raw.get("variety", "")).strip(),
            grade=str(raw.get("grade", "")).strip(),
            arrival_date=str(raw.get("arrival_date", "")).strip(),
            min_price=float(raw.get("min_price", 0)),
            max_price=float(raw.get("max_price", 0)),
            modal_price=float(raw.get("modal_price", 0)),
        )
    except (ValueError, TypeError) as exc:
        logger.warning("Skipping malformed record %s: %s", raw, exc)
        return None


def _build_params(
    state: str | None,
    district: str | None,
    commodity: str | None,
    market: str | None,
    variety: str | None,
    limit: int,
    offset: int,
) -> dict[str, str]:
    """Build query parameters for the data.gov.in API."""
    params: dict[str, str] = {
        "api-key": settings.data_gov_api_key,
        "format": "json",
        "limit": str(min(limit, 500)),
        "offset": str(offset),
    }

    filters: dict[str, str] = {}
    if state:
        filters["state"] = state
    if district:
        filters["district"] = district
    if commodity:
        filters["commodity"] = commodity
    if market:
        filters["market"] = market
    if variety:
        filters["variety"] = variety

    for field, value in filters.items():
        params[f"filters[{field}]"] = value

    return params


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_mandi_prices(
    state: str | None = None,
    district: str | None = None,
    commodity: str | None = None,
    market: str | None = None,
    variety: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """
    Fetch current mandi prices from the Government of India Open Data API.

    Returns:
        {
            "status": "ok" | "no_results" | "error",
            "total": int,
            "records": list[MandiRecord],
            "message": str,
        }
    """
    if not settings.data_gov_api_key:
        return {
            "status": "error",
            "total": 0,
            "records": [],
            "message": "DATA_GOV_API_KEY is not configured.",
        }

    params = _build_params(state, district, commodity, market, variety, limit, offset)

    try:
        response = requests.get(_BASE_URL, params=params, headers=_HEADERS, timeout=_TIMEOUT_SECONDS)

        if response.status_code == 429:
            return {
                "status": "error",
                "total": 0,
                "records": [],
                "message": "Government API rate limit reached. Please try again shortly.",
            }

        if response.status_code == 403:
            return {
                "status": "error",
                "total": 0,
                "records": [],
                "message": "Invalid or unauthorized DATA_GOV_API_KEY.",
            }

        response.raise_for_status()
        data = response.json()

    except Timeout:
        logger.error("data.gov.in API timed out after %ss", _TIMEOUT_SECONDS)
        return {
            "status": "error",
            "total": 0,
            "records": [],
            "message": "Government market data API timed out. Please try again.",
        }
    except ConnectionError as exc:
        logger.error("data.gov.in connection error: %s", exc)
        return {
            "status": "error",
            "total": 0,
            "records": [],
            "message": "Could not reach the Government market data API. Check your network.",
        }
    except HTTPError as exc:
        logger.error("data.gov.in HTTP error: %s", exc)
        return {
            "status": "error",
            "total": 0,
            "records": [],
            "message": f"Government API returned an error ({exc.response.status_code}).",
        }
    except (RequestException, ValueError) as exc:
        logger.error("data.gov.in request/parse error: %s", exc)
        return {
            "status": "error",
            "total": 0,
            "records": [],
            "message": "Received an unexpected error from the Government API.",
        }

    # -- Parse response --
    total = int(data.get("total", 0))
    raw_records: list[dict] = data.get("records", []) or []

    if total == 0 or not raw_records:
        parts = [p for p in [commodity, district, state] if p]
        subject = " in ".join(parts) if parts else "this query"
        return {
            "status": "no_results",
            "total": 0,
            "records": [],
            "message": f"No current mandi records found for {subject}.",
        }

    records = [r for raw in raw_records if (r := _normalize_record(raw)) is not None]

    return {
        "status": "ok",
        "total": total,
        "records": records,
        "message": f"Found {len(records)} record(s).",
    }
