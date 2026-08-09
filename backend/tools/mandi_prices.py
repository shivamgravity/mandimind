"""
mandi_prices.py — Tool: fetch current mandi prices from data.gov.in.

Returns structured results including a 'no_results' status so Gemma
can decide whether to expand the search radius.
"""

# TODO: Implement get_mandi_prices()
# - Call data_gov.py client
# - If district + commodity → no records → return {"status": "no_results", ...}
# - If results found → return {"status": "ok", "records": [...MandiRecord]}
