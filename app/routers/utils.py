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
    rate = MOCK_RATES.get((from_currency, to_currency))
    if not rate:
        return {"error": "Rate not available"}

    return {
        "amount": amount,
        "from": from_currency,
        "to": to_currency,
        "converted_amount": amount * rate,
        "rate": rate,
    }
