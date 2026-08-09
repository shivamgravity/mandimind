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

def chat(
    user_message: str,
    history: list[dict] | None = None,
) -> AgentResponse:
    """
    Run a single agentic turn with Gemma 4.

    Args:
        user_message:  The farmer's message (English or Hindi).
        history:       Previous conversation turns as list of
                       {"role": "user"|"model", "text": str}.

    Returns:
        AgentResponse with the final reply, tool calls made, and
        the pipeline result if rank_market_options was called.
    """
    client = _get_client()
    model = settings.gemma_model

    # Build conversation history
    contents: list[types.Content] = []

    if history:
        for turn in history:
            role = turn.get("role", "user")
            text = turn.get("text", "")
            if text:
                contents.append(
                    types.UserContent(parts=[types.Part(text=text)])
                    if role == "user"
                    else types.ModelContent(parts=[types.Part(text=text)])
                )

    # Add current user message
    contents.append(types.UserContent(parts=[types.Part(text=user_message)]))

    tool_calls_made: list[str] = []
    pipeline_result: dict | None = None
    final_reply: str = ""

    # Agentic loop
    for iteration in range(_MAX_ITERATIONS):
        logger.info("Agent iteration %d/%d", iteration + 1, _MAX_ITERATIONS)

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[_ALL_TOOLS],
                temperature=0.2,  # Low temp for factual tool-use
            ),
        )

        candidate = response.candidates[0]
        model_parts = candidate.content.parts

        # Separate text parts from function call parts
        text_parts = [p for p in model_parts if p.text]
        fc_parts   = [p for p in model_parts if p.function_call]

        # If no function calls — Gemma is done, return the text reply
        if not fc_parts:
            final_reply = "\n".join(p.text for p in text_parts if p.text).strip()
            break

        # Append the model's turn to conversation history.
        # CRITICAL: Strip internal 'thought' parts — sending them back to the API
        # causes a '400 Corrupted thought signature' error on Gemma thinking models.
        safe_parts = [p for p in model_parts if p.function_call or (p.text and not getattr(p, 'thought', False))]
        contents.append(types.ModelContent(parts=safe_parts))

        # Execute each function call and collect responses
        tool_response_parts: list[types.Part] = []

        for part in fc_parts:
            fc = part.function_call
            fn_name = fc.name
            fn_args = dict(fc.args)

            logger.info("Gemma called tool: %s(%s)", fn_name, fn_args)
            tool_calls_made.append(fn_name)

            result = _dispatch_tool(fn_name, fn_args)

            # Save pipeline result for the frontend
            if fn_name == "rank_market_options":
                pipeline_result = result

            # Serialize result to JSON string for Gemma
            result_str = json.dumps(result, default=str, ensure_ascii=False)

            tool_response_parts.append(
                types.Part(
                    function_response=types.FunctionResponse(
                        name=fn_name,
                        response={"result": result_str},
                    )
                )
            )

        # Append tool responses as a user turn
        contents.append(types.UserContent(parts=tool_response_parts))

    else:
        # Hit max iterations — extract whatever text we have
        logger.warning("Agent hit max iterations (%d)", _MAX_ITERATIONS)
        final_reply = (
            "I was unable to complete the analysis within the allowed steps. "
            "Please try again."
        )

    return AgentResponse(
        reply=final_reply,
        tool_calls_made=tool_calls_made,
        pipeline_result=pipeline_result,
    )
