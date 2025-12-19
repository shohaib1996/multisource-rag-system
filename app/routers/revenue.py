from fastapi import APIRouter
from sqlalchemy.orm import Session
from fastapi import Depends
from sqlalchemy import text
from app.db import get_db
from app.schemas.internal import RevenueSummaryResponse
from typing import List

router = APIRouter()


@router.get(
    "/revenue/summary",
    response_model=List[RevenueSummaryResponse],
    summary="Get revenue summary for date range",
    description="Internal tool: Used by admin AI to calculate revenue",
)
def revenue_summary(start_date: str, end_date: str, db: Session = Depends(get_db)):
    query = text("""
        SELECT
            COUNT(*) AS total_payments,
            COALESCE(SUM(amount), 0) AS total_revenue,
            currency
        FROM payments
        WHERE payment_status = 'paid'
          AND created_at BETWEEN :start AND :end
        GROUP BY currency
    """)
    rows = db.execute(query, {"start": start_date, "end": end_date}).fetchall()

    return [dict(row._mapping) for row in rows]
