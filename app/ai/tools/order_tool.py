import requests
from langchain.tools import tool

INTERNAL_API_BASE = "http://127.0.0.1:8000/internal"


@tool
def get_order_status(order_id: int) -> dict:
    """
    Get order status, amount, currency, and creation date using order ID.
    """
    response = requests.get(f"{INTERNAL_API_BASE}/orders/{order_id}")
    response.raise_for_status()
    return response.json()
