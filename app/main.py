from fastapi import FastAPI
from app.routers import orders, revenue, utils

app = FastAPI(title="Internal APIs")

app.include_router(orders.router, prefix="/internal")
app.include_router(revenue.router, prefix="/internal")
app.include_router(utils.router, prefix="/internal")
