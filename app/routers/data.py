from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db import get_db
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import os

router = APIRouter()

KNOWLEDGE_BASE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "knowledge_base"
)


class OrderItem(BaseModel):
    order_id: int
    status: str
    total_amount: float
    currency: str
    user_id: int
    created_at: datetime


class OrdersResponse(BaseModel):
    orders: list[OrderItem]
    total: int


class PaymentItem(BaseModel):
    id: int
    order_id: int
    provider: str
    payment_method: Optional[str]
    payment_status: str
    amount: float
    currency: str
    paid_at: Optional[datetime]
    created_at: datetime


class PaymentsResponse(BaseModel):
    payments: list[PaymentItem]
    total: int


class KnowledgeFile(BaseModel):
    filename: str
    title: str
    content: str
    size_bytes: int


class KnowledgeFilesResponse(BaseModel):
    files: list[KnowledgeFile]
    total: int


@router.get(
    "/orders",
    response_model=OrdersResponse,
    summary="Get all orders",
    description="Fetch all orders from the database to show users what order data is available",
)
def get_all_orders(db: Session = Depends(get_db)):
    query = text("""
        SELECT id, user_id, status, total_amount, currency, created_at
        FROM orders
        ORDER BY created_at DESC
    """)
    results = db.execute(query).fetchall()

    orders = [
        OrderItem(
            order_id=row.id,
            user_id=row.user_id,
            status=row.status,
            total_amount=float(row.total_amount),
            currency=row.currency,
            created_at=row.created_at,
        )
        for row in results
    ]

    return OrdersResponse(orders=orders, total=len(orders))


@router.get(
    "/payments",
    response_model=PaymentsResponse,
    summary="Get all payments",
    description="Fetch all payments from the database to show users what payment/revenue data is available",
)
def get_all_payments(db: Session = Depends(get_db)):
    query = text("""
        SELECT id, order_id, provider, payment_method, payment_status, amount, currency, paid_at, created_at
        FROM payments
        ORDER BY created_at DESC
    """)
    results = db.execute(query).fetchall()

    payments = [
        PaymentItem(
            id=row.id,
            order_id=row.order_id,
            provider=row.provider,
            payment_method=row.payment_method,
            payment_status=row.payment_status,
            amount=float(row.amount),
            currency=row.currency,
            paid_at=row.paid_at,
            created_at=row.created_at,
        )
        for row in results
    ]

    return PaymentsResponse(payments=payments, total=len(payments))


@router.get(
    "/knowledge-files",
    response_model=KnowledgeFilesResponse,
    summary="Get all knowledge base files",
    description="List all knowledge base documents that are ingested into Pinecone for RAG queries",
)
def get_knowledge_files():
    files = []
    knowledge_dir = os.path.abspath(KNOWLEDGE_BASE_DIR)

    if os.path.exists(knowledge_dir):
        for filename in os.listdir(knowledge_dir):
            filepath = os.path.join(knowledge_dir, filename)
            if os.path.isfile(filepath) and filename.endswith(".txt"):
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                title = filename.replace("_", " ").replace(".txt", "").title()

                files.append(
                    KnowledgeFile(
                        filename=filename,
                        title=title,
                        content=content,
                        size_bytes=os.path.getsize(filepath),
                    )
                )

    # Sort by filename
    files.sort(key=lambda x: x.filename)

    return KnowledgeFilesResponse(files=files, total=len(files))
