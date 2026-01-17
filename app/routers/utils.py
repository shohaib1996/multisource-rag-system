from fastapi import APIRouter
from app.schemas.internal import CurrencyConversionResponse

router = APIRouter()

MOCK_RATES = {
    ("USD", "BDT"): 120.5,
    ("USD", "EUR"): 0.92,
}


@router.get(
    "/utils/convert-currency",
    response_model=CurrencyConversionResponse,
    summary="Convert currency",
    description="Internal tool: Convert amount between currencies",
)
def convert(amount: float, from_currency: str, to_currency: str):
    # Normalize to uppercase
    from_curr = from_currency.upper()
    to_curr = to_currency.upper()

    rate = MOCK_RATES.get((from_curr, to_curr))
    if not rate:
        return {"error": f"Rate not available for {from_curr} to {to_curr}"}

    return {
        "amount": amount,
        "from_currency": from_curr,
        "to_currency": to_curr,
        "converted_amount": amount * rate,
        "rate": rate,
    }
