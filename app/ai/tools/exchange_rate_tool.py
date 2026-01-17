import requests
from langchain.tools import tool


@tool
def get_live_exchange_rate(from_currency: str, to_currency: str) -> dict:
    """
    Get live exchange rate from an external API.
    Uses the free frankfurter.app API for real-time rates.

    Args:
        from_currency: Source currency code (e.g., USD, EUR, GBP)
        to_currency: Target currency code (e.g., BDT, EUR, JPY)
    """
    try:
        # Frankfurter API - free, no API key required
        url = "https://api.frankfurter.app/latest"
        params = {"from": from_currency.upper(), "to": to_currency.upper()}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        rate = data["rates"].get(to_currency.upper())

        return {
            "from": from_currency.upper(),
            "to": to_currency.upper(),
            "rate": rate,
            "date": data.get("date"),
            "source": "frankfurter.app",
        }
    except requests.RequestException as e:
        return {"error": f"Failed to fetch exchange rate: {str(e)}"}


@tool
def convert_with_live_rate(amount: float, from_currency: str, to_currency: str) -> dict:
    """
    Convert currency using live exchange rates from external API.

    Args:
        amount: The amount to convert
        from_currency: Source currency code (e.g., USD)
        to_currency: Target currency code (e.g., EUR)
    """
    try:
        url = "https://api.frankfurter.app/latest"
        params = {
            "amount": amount,
            "from": from_currency.upper(),
            "to": to_currency.upper(),
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        converted = data["rates"].get(to_currency.upper())

        return {
            "amount": amount,
            "from": from_currency.upper(),
            "to": to_currency.upper(),
            "converted_amount": converted,
            "date": data.get("date"),
            "source": "frankfurter.app (live)",
        }
    except requests.RequestException as e:
        return {"error": f"Failed to convert currency: {str(e)}"}


if __name__ == "__main__":
    # Test the tools
    print("=== Exchange Rate Test ===")
    print(get_live_exchange_rate.invoke({"from_currency": "USD", "to_currency": "EUR"}))

    print("\n=== Conversion Test ===")
    print(
        convert_with_live_rate.invoke(
            {"amount": 100, "from_currency": "USD", "to_currency": "EUR"}
        )
    )
