"""
market_locations.py — Tool: look up market GPS coordinates from local CSV.

The CSV (data/market_locations.csv) covers the UP mandis needed for the demo.
The Government API remains the source of truth for prices.
"""

# TODO: Implement:
# - get_market_location(market, district, state) → MarketLocation | None
# - find_nearby_candidate_markets(origin_lat, origin_lon, candidates, max_km) → list[MarketCandidate]
# - load_origin_location(city_name) → (lat, lon) — small lookup for known UP cities
