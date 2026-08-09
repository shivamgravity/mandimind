"""
schemas.py — Shared Pydantic models for request/response data.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, field_validator


# ---------------------------------------------------------------------------
# Mandi price record (normalised from data.gov.in response)
# ---------------------------------------------------------------------------

class MandiRecord(BaseModel):
    state: str
    district: str
    market: str
    commodity: str
    variety: str
    grade: str
    arrival_date: str
    min_price: float
    max_price: float
    modal_price: float

    @field_validator("min_price", "max_price", "modal_price", mode="before")
    @classmethod
    def round_price(cls, v: float) -> float:
        """Round floating-point artefacts (e.g. 2518.1399999 → 2518.14)."""
        return round(float(v), 2)


# ---------------------------------------------------------------------------
# Market location
# ---------------------------------------------------------------------------

class MarketLocation(BaseModel):
    market: str
    district: str
    state: str
    latitude: float
    longitude: float
    source: str = "market_locations.csv"


# ---------------------------------------------------------------------------
# Market comparison candidate (one market with full calculated data)
# ---------------------------------------------------------------------------

class MarketCandidate(BaseModel):
    market: str
    district: str
    state: str
    modal_price: float
    min_price: float
    max_price: float
    variety: str
    arrival_date: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_km: Optional[float] = None
    estimated_transport_cost: Optional[float] = None
    gross_value: Optional[float] = None
    estimated_net_return: Optional[float] = None
    location_available: bool = True


# ---------------------------------------------------------------------------
# API request / response models
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    location: str
    commodity: str
    quantity_quintals: float
    search_radius_km: float = 150.0
    state: str = "Uttar Pradesh"

    @field_validator("quantity_quintals")
    @classmethod
    def positive_quantity(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Quantity must be a positive number.")
        return v


class AgentChatRequest(BaseModel):
    message: str
    history: list[dict] = []


class AgentChatResponse(BaseModel):
    reply: str
    tool_calls_made: list[str] = []
    candidates: list[MarketCandidate] = []
    top_recommendation: Optional[MarketCandidate] = None
