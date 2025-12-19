from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from sqlalchemy import text
from app.schemas.internal import OrderStatusResponse

router = APIRouter()


@router.get(
    "/orders/{order_id}",
    response_model=OrderStatusResponse,
    summary="Get order status by order ID",
    description="Internal tool: Fetch order status, amount, currency, and creation date",
)
def get_order(order_id: int, db: Session = Depends(get_db)):
    query = text("""
        SELECT id, status, total_amount, currency, created_at
        FROM orders
        WHERE id = :order_id
    """)
    result = db.execute(query, {"order_id": order_id}).fetchone()

    if not result:
        return {"error": "Order not found"}

    return dict(result._mapping)
