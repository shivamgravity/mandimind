"""
returns.py — Tool: calculate gross value and estimated net return.

Formula:
    gross_value          = quantity_quintals × modal_price
    estimated_net_return = gross_value - estimated_transport_cost

Gemma must NOT perform this arithmetic — it is done here deterministically.
"""


def calculate_estimated_return(
    quantity_quintals: float,
    modal_price: float,
    estimated_transport_cost: float,
) -> dict:
    """
    Calculate gross value and estimated net return for selling at a mandi.

    Args:
        quantity_quintals:        Quantity of produce in quintals.
        modal_price:              Current government modal price (₹/quintal).
        estimated_transport_cost: Estimated transport cost (₹).

    Returns:
        dict with keys:
            quantity_quintals, modal_price, gross_value,
            estimated_transport_cost, estimated_net_return
    """
    gross_value = round(quantity_quintals * modal_price, 2)
    net_return = round(gross_value - estimated_transport_cost, 2)

    return {
        "quantity_quintals": quantity_quintals,
        "modal_price": modal_price,
        "gross_value": gross_value,
        "estimated_transport_cost": estimated_transport_cost,
        "estimated_net_return": net_return,
    }
