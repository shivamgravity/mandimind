"""
gemma_agent.py — MandiMind Gemma 4 agent with function calling.

Uses the Google GenAI Python SDK (google-genai >= 2.0).
Model: gemma-4-26b-a4b-it

Architecture:
  - All tool SCHEMAS are defined here (what Gemma can call)
  - All tool IMPLEMENTATIONS live in backend/tools/ and backend/services/
  - Gemma orchestrates; Python does all deterministic arithmetic
  - Agentic loop runs until Gemma produces a final text response
    or the max iteration cap is hit (safety guard)
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from google import genai
from google.genai import types

from backend.config import settings
from backend.agent.prompts import SYSTEM_PROMPT
from backend.tools.mandi_prices import get_mandi_prices
from backend.tools.market_locations import get_origin_coordinates, get_market_location
from backend.tools.distance import haversine_distance
from backend.tools.transport import estimate_transport_cost
from backend.tools.returns import calculate_estimated_return
from backend.services.pipeline import rank_market_options

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Max tool-call iterations (safety guard — prevents infinite loops)
# ---------------------------------------------------------------------------
_MAX_ITERATIONS = 10


# ---------------------------------------------------------------------------
# Tool definitions (schemas Gemma sees)
# ---------------------------------------------------------------------------

_TOOL_GET_MANDI_PRICES = types.FunctionDeclaration(
    name="get_mandi_prices",
    description=(
        "Retrieve current government mandi prices from the Government of India "
        "Open Data Platform. Returns structured price records or a no_results "
        "status if no data is available for the given filters."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "state": types.Schema(
                type="STRING",
                description="Indian state name, e.g. 'Uttar Pradesh'",
            ),
            "commodity": types.Schema(
                type="STRING",
                description="Crop/commodity name, e.g. 'Wheat', 'Potato', 'Tomato'",
            ),
            "district": types.Schema(
                type="STRING",
                description=(
                    "Optional: district name to narrow the search, e.g. 'Prayagraj'. "
                    "Omit to search the entire state."
                ),
            ),
        },
        required=["state", "commodity"],
    ),
)

_TOOL_RANK_MARKET_OPTIONS = types.FunctionDeclaration(
    name="rank_market_options",
    description=(
        "Run the full market comparison pipeline: fetches current prices, "
        "resolves market coordinates, calculates distances, estimates transport costs, "
        "calculates gross value and estimated net return, and returns markets ranked "
        "by estimated net return. Use this as the primary tool when the farmer asks "
        "where to sell. It handles the local→state-wide fallback automatically."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "origin": types.Schema(
                type="STRING",
                description="Farmer's city or district name, e.g. 'Prayagraj'",
            ),
            "state": types.Schema(
                type="STRING",
                description="Indian state name, e.g. 'Uttar Pradesh'",
            ),
            "commodity": types.Schema(
                type="STRING",
                description="Crop name, e.g. 'Wheat'",
            ),
            "quantity_quintals": types.Schema(
                type="NUMBER",
                description="Quantity of produce the farmer wants to sell, in quintals",
            ),
            "search_radius_km": types.Schema(
                type="NUMBER",
                description=(
                    "Maximum distance from farmer's location to consider, in km. "
                    "Default is 150 km. Increase if no results found."
                ),
            ),
        },
        required=["origin", "state", "commodity", "quantity_quintals"],
    ),
)

_TOOL_CALCULATE_DISTANCE = types.FunctionDeclaration(
    name="calculate_distance",
    description=(
        "Calculate the approximate straight-line (Haversine) distance between "
        "two GPS coordinate pairs. Returns distance in kilometres. "
        "Note: this is geographic distance, NOT driving distance."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "lat1": types.Schema(type="NUMBER", description="Origin latitude"),
            "lon1": types.Schema(type="NUMBER", description="Origin longitude"),
            "lat2": types.Schema(type="NUMBER", description="Destination latitude"),
            "lon2": types.Schema(type="NUMBER", description="Destination longitude"),
        },
        required=["lat1", "lon1", "lat2", "lon2"],
    ),
)

_TOOL_ESTIMATE_TRANSPORT = types.FunctionDeclaration(
    name="estimate_transport_cost",
    description=(
        "Estimate the transportation cost for moving produce to a mandi. "
        "Uses a configurable prototype rate. "
        "This is an estimate — NOT an official government rate."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "distance_km": types.Schema(
                type="NUMBER", description="Distance to market in km"
            ),
            "quantity_quintals": types.Schema(
                type="NUMBER", description="Quantity of produce in quintals"
            ),
        },
        required=["distance_km", "quantity_quintals"],
    ),
)

_TOOL_CALCULATE_RETURN = types.FunctionDeclaration(
    name="calculate_estimated_return",
    description=(
        "Calculate gross value and estimated net return for selling at a mandi. "
        "Formula: gross_value = quantity × modal_price; "
        "net_return = gross_value - transport_cost."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "quantity_quintals": types.Schema(
                type="NUMBER", description="Quantity in quintals"
            ),
            "modal_price": types.Schema(
                type="NUMBER", description="Government modal price in ₹/quintal"
            ),
            "estimated_transport_cost": types.Schema(
                type="NUMBER", description="Estimated transport cost in ₹"
            ),
        },
        required=["quantity_quintals", "modal_price", "estimated_transport_cost"],
    ),
)

_ALL_TOOLS = types.Tool(
    function_declarations=[
        _TOOL_GET_MANDI_PRICES,
        _TOOL_RANK_MARKET_OPTIONS,
    ]
)


# ---------------------------------------------------------------------------
# Tool dispatcher — maps Gemma's function call names to Python implementations
# ---------------------------------------------------------------------------

def _dispatch_tool(name: str, args: dict) -> Any:
    """Execute the named tool with the given arguments and return the result."""
    try:
        if name == "get_mandi_prices":
            return get_mandi_prices(
                state=args["state"],
                commodity=args["commodity"],
                district=args.get("district"),
                limit=10,
            )

        elif name == "rank_market_options":
            return rank_market_options(
                origin=args["origin"],
                state=args["state"],
                commodity=args["commodity"],
                quantity_quintals=float(args["quantity_quintals"]),
                search_radius_km=float(args.get("search_radius_km", settings.default_search_radius_km)),
            )

        elif name == "calculate_distance":
            dist = haversine_distance(
                float(args["lat1"]), float(args["lon1"]),
                float(args["lat2"]), float(args["lon2"]),
            )
            return {"distance_km": dist, "note": "Approximate geographic (straight-line) distance."}

        elif name == "estimate_transport_cost":
            return estimate_transport_cost(
                distance_km=float(args["distance_km"]),
                quantity_quintals=float(args["quantity_quintals"]),
            )

        elif name == "calculate_estimated_return":
            return calculate_estimated_return(
                quantity_quintals=float(args["quantity_quintals"]),
                modal_price=float(args["modal_price"]),
                estimated_transport_cost=float(args["estimated_transport_cost"]),
            )

        else:
            logger.warning("Unknown tool called: %s", name)
            return {"error": f"Unknown tool: {name}"}

    except Exception as exc:
        logger.error("Tool %s failed: %s", name, exc, exc_info=True)
        return {"error": f"Tool execution failed: {exc}"}


# ---------------------------------------------------------------------------
# Gemma 4 client (singleton)
# ---------------------------------------------------------------------------

def _get_client() -> genai.Client:
    api_key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")
    return genai.Client(api_key=api_key)


# ---------------------------------------------------------------------------
# Agent response dataclass
# ---------------------------------------------------------------------------

class AgentResponse:
    def __init__(
        self,
        reply: str,
        tool_calls_made: list[str],
        pipeline_result: dict | None,
    ):
        self.reply = reply
        self.tool_calls_made = tool_calls_made
        self.pipeline_result = pipeline_result  # last rank_market_options result if called

    def to_dict(self) -> dict:
        return {
            "reply": self.reply,
            "tool_calls_made": self.tool_calls_made,
            "pipeline_result": self.pipeline_result,
        }


# ---------------------------------------------------------------------------
# Main agentic loop
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Main chat function — Direct pipeline + single LLM summarisation call
# ---------------------------------------------------------------------------
# Architecture:
#   1. Parse crop/quantity/location from the user message directly
#   2. Run rank_market_options() in Python (no LLM needed for this)
#   3. Make ONE stateless LLM call to generate a natural language summary
#
# This eliminates multi-turn conversation history entirely, which permanently
# fixes the '400 Corrupted thought signature' error that occurs when Gemma's
# internal reasoning tokens are fed back into a subsequent API request.
# ---------------------------------------------------------------------------

def _parse_query(user_message: str) -> dict | None:
    """
    Extract origin, state, commodity, quantity from a natural language message.
    Returns a dict or None if parsing fails.
    """
    import re

    msg = user_message.lower()

    # Quantity — look for a number before 'quintal'
    qty_match = re.search(r'(\d+(?:\.\d+)?)\s*quintal', msg)
    quantity = float(qty_match.group(1)) if qty_match else None

    # Commodity — look for known crops
    crops = ["wheat", "potato", "tomato", "onion", "rice", "maize", "soybean",
             "mustard", "barley", "jowar", "bajra", "cotton", "sugarcane",
             "gehu", "aloo", "pyaaz", "chawal"]
    commodity = None
    for crop in crops:
        if crop in msg:
            commodity = crop.capitalize()
            break

    # State
    state = "Uttar Pradesh"
    if "madhya pradesh" in msg or " mp " in msg:
        state = "Madhya Pradesh"
    elif "punjab" in msg:
        state = "Punjab"
    elif "haryana" in msg:
        state = "Haryana"
    elif "rajasthan" in msg:
        state = "Rajasthan"

    # Radius
    radius_match = re.search(r'(\d+)\s*km', msg)
    radius = float(radius_match.group(1)) if radius_match else settings.default_search_radius_km

    # Origin — everything after "in " or "from "
    origin = None
    for pattern in [r'(?:i am in|from|in)\s+([a-z\s]+?)(?:,|\.|please|find|and|$)', ]:
        m = re.search(pattern, msg)
        if m:
            origin = m.group(1).strip().title()
            break

    if not origin or not commodity or not quantity:
        return None

    return {
        "origin": origin,
        "state": state,
        "commodity": commodity,
        "quantity_quintals": quantity,
        "search_radius_km": radius,
    }


def chat(
    user_message: str,
    history: list[dict] | None = None,
) -> AgentResponse:
    """
    Run a single turn: parse query → run Python pipeline → LLM summarises result.

    Args:
        user_message:  The farmer's message (English or Hindi).
        history:       Ignored in this architecture (kept for API compatibility).

    Returns:
        AgentResponse with the final reply, tool calls made, and pipeline result.
    """
    client = _get_client()
    model = settings.gemma_model

    tool_calls_made: list[str] = []
    pipeline_result: dict | None = None

    # Step 1 — Parse the query from natural language
    query = _parse_query(user_message)

    if not query:
        # Fallback: ask LLM to extract and respond (simple, no tools)
        response = client.models.generate_content(
            model=model,
            contents=[types.UserContent(parts=[types.Part(text=user_message)])],
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are MandiMind, an agricultural assistant for Indian farmers. "
                    "Ask the user politely for their crop name, quantity in quintals, "
                    "and their city/location so you can find the best mandi for them."
                ),
                temperature=0.3,
            ),
        )
        reply = response.candidates[0].content.parts[-1].text.strip()
        return AgentResponse(reply=reply, tool_calls_made=[], pipeline_result=None)

    # Step 2 — Run the Python pipeline directly (no LLM tool call needed)
    logger.info("Running pipeline: %s", query)
    tool_calls_made.append("rank_market_options")

    try:
        pipeline_result = rank_market_options(
            origin=query["origin"],
            state=query["state"],
            commodity=query["commodity"],
            quantity_quintals=query["quantity_quintals"],
            search_radius_km=query["search_radius_km"],
        )
    except Exception as exc:
        logger.error("Pipeline failed: %s", exc, exc_info=True)
        return AgentResponse(
            reply="I encountered an error while fetching market data. Please try again.",
            tool_calls_made=tool_calls_made,
            pipeline_result=None,
        )

    # Step 3 — Single stateless LLM call to write a natural language summary
    if pipeline_result and pipeline_result.get("status") == "ok":
        top = pipeline_result.get("top_recommendation", {})
        markets = pipeline_result.get("ranked_markets", [])[:3]

        summary_prompt = (
            f"A farmer in {query['origin']} wants to sell {query['quantity_quintals']} quintals "
            f"of {query['commodity']}. Here are the top 3 markets ranked by estimated net return:\n\n"
        )
        for i, m in enumerate(markets):
            summary_prompt += (
                f"{i+1}. {m.get('market')} ({m.get('district')}): "
                f"Modal Price ₹{m.get('modal_price')}/q, "
                f"Distance {m.get('distance_km', 0):.1f} km, "
                f"Transport Cost ₹{m.get('estimated_transport_cost', 0):.0f}, "
                f"Net Return ₹{m.get('estimated_net_return', 0):.0f}\n"
            )
        summary_prompt += (
            "\nWrite a 2-sentence recommendation for the farmer explaining which market "
            "is best and briefly why (considering price vs transport cost tradeoff). "
            "Be concise and direct. Do not use bullet points or tables."
        )

        try:
            summary_response = client.models.generate_content(
                model=model,
                contents=[types.UserContent(parts=[types.Part(text=summary_prompt)])],
                config=types.GenerateContentConfig(temperature=0.3),
            )
            # Get last text part to skip any thought parts
            text_parts = [
                p.text for p in summary_response.candidates[0].content.parts
                if p.text and not getattr(p, 'thought', False)
            ]
            final_reply = text_parts[-1].strip() if text_parts else (
                f"Based on current data, I recommend selling at {top.get('market')} "
                f"for the highest estimated net return of ₹{top.get('estimated_net_return', 0):,.0f}."
            )
        except Exception as exc:
            logger.warning("LLM summary failed, using fallback: %s", exc)
            final_reply = (
                f"Based on current data, I recommend selling your {query['quantity_quintals']} quintals "
                f"of {query['commodity']} at {top.get('market', 'the top market')}. "
                f"It offers the highest estimated net return of "
                f"₹{top.get('estimated_net_return', 0):,.0f}."
            )
    else:
        msg = pipeline_result.get("message", "No markets found.") if pipeline_result else "Pipeline returned no data."
        final_reply = f"I could not find suitable markets for your query. {msg}"

    return AgentResponse(
        reply=final_reply,
        tool_calls_made=tool_calls_made,
        pipeline_result=pipeline_result,
    )

