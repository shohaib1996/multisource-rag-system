import requests
from langchain.tools import tool

INTERNAL_API_BASE = "http://127.0.0.1:8000/internal"


@tool
def get_revenue_summary(start_date: str, end_date: str) -> list:
    """
    Get revenue summary for a date range.
    Returns total payments and revenue grouped by currency.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    response = requests.get(
        f"{INTERNAL_API_BASE}/revenue/summary",
        params={"start_date": start_date, "end_date": end_date}
    )
    response.raise_for_status()
    return response.json()
