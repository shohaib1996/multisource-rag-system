from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class OrderStatusResponse(BaseModel):
    order_id: int
    status: str
    total_amount: float
    currency: str
    created_at: datetime


class RevenueSummaryResponse(BaseModel):
    total_payments: int
    total_revenue: float
    currency: str


class CurrencyConversionResponse(BaseModel):
    amount: float
    from_currency: str
    to_currency: str
    converted_amount: float
    rate: float
