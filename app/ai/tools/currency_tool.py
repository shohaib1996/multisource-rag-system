import requests
from langchain.tools import tool

INTERNAL_API_BASE = "http://127.0.0.1:8000/internal"


@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """
    Convert an amount from one currency to another.

    Args:
        amount: The amount to convert
        from_currency: Source currency code (e.g., USD)
        to_currency: Target currency code (e.g., BDT, EUR)
    """
    response = requests.get(
        f"{INTERNAL_API_BASE}/utils/convert-currency",
        params={
            "amount": amount,
            "from_currency": from_currency,
            "to_currency": to_currency
        }
    )
    response.raise_for_status()
    return response.json()
