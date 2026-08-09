"""
main.py — FastAPI application entrypoint for MandiMind.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from backend.config import settings
from backend.agent.gemma_agent import chat as agent_chat
from backend.services.pipeline import rank_market_options
from backend.tools.mandi_prices import get_mandi_prices

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MandiMind API",
    description=(
        "Agricultural decision-support agent powered by Gemma 4 "
        "and Government of India mandi data."
    ),
    version="0.1.0",
)

# Allow frontend to connect (local dev + Vercel production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message cannot be empty.")
        return v.strip()


class ChatResponse(BaseModel):
    reply: str
    tool_calls_made: list[str] = []
    pipeline_result: dict | None = None


class CompareRequest(BaseModel):
    origin: str
    state: str = "Uttar Pradesh"
    commodity: str
    quantity_quintals: float
    search_radius_km: float = 150.0

    @field_validator("quantity_quintals")
    @classmethod
    def positive_quantity(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Quantity must be a positive number.")
        return v


class PricesRequest(BaseModel):
    state: str
    commodity: str
    district: str | None = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict:
    """Health check — confirms API is running."""
    return {"status": "ok", "service": "MandiMind API", "version": "0.1.0"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest) -> ChatResponse:
    """
    Conversational Gemma 4 agent endpoint.

    The agent will call tools internally, run the full pipeline,
    and return a natural-language recommendation.
    """
    try:
        result = agent_chat(
            user_message=req.message,
            history=req.history,
        )
        return ChatResponse(
            reply=result.reply,
            tool_calls_made=result.tool_calls_made,
            pipeline_result=result.pipeline_result,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Agent error: %s", exc)
        # Check if it's a google.genai API error (e.g. Rate Limit)
        if hasattr(exc, 'status_code') and exc.status_code == 429:
            raise HTTPException(
                status_code=429,
                detail="Gemini API rate limit exceeded. Please wait a minute and try again."
            )
        # Check by string match just in case
        if "429 RESOURCE_EXHAUSTED" in str(exc) or "quota" in str(exc).lower():
            raise HTTPException(
                status_code=429,
                detail="Gemini API rate limit exceeded. Please wait a minute and try again."
            )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again.",
        )


@app.post("/api/compare")
async def compare_endpoint(req: CompareRequest) -> dict:
    """
    Direct market comparison pipeline endpoint (no Gemma).

    Returns the full ranked market list — useful for the frontend
    to render the comparison table independently of the chat flow.
    """
    try:
        result = rank_market_options(
            origin=req.origin,
            state=req.state,
            commodity=req.commodity,
            quantity_quintals=req.quantity_quintals,
            search_radius_km=req.search_radius_km,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Pipeline error: %s", exc)
        raise HTTPException(status_code=500, detail="Pipeline execution failed.")


@app.post("/api/prices")
async def prices_endpoint(req: PricesRequest) -> dict:
    """
    Direct mandi price lookup endpoint.

    Returns current government price records for a commodity in a state/district.
    """
    try:
        return get_mandi_prices(
            state=req.state,
            commodity=req.commodity,
            district=req.district,
            limit=100,
        )
    except Exception as exc:
        logger.exception("Prices error: %s", exc)
        raise HTTPException(status_code=500, detail="Price lookup failed.")
