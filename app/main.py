import asyncio
import logging
import os

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import orders, revenue, utils, agent, data

logger = logging.getLogger(__name__)

RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
PING_INTERVAL = 10 * 60  # 14 minutes (Render sleeps after 15 min of inactivity)


async def keep_alive():
    """Periodically ping our own health endpoint to prevent Render free-tier spin-down."""
    if not RENDER_EXTERNAL_URL:
        logger.info("RENDER_EXTERNAL_URL not set — keep-alive ping disabled.")
        return
    url = f"{RENDER_EXTERNAL_URL}/"
    logger.info("Keep-alive started: pinging %s every %s seconds", url, PING_INTERVAL)
    async with httpx.AsyncClient() as client:
        while True:
            await asyncio.sleep(PING_INTERVAL)
            try:
                resp = await client.get(url, timeout=10)
                logger.info("Keep-alive ping: %s", resp.status_code)
            except Exception as exc:
                logger.warning("Keep-alive ping failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(keep_alive())
    yield
    task.cancel()


app = FastAPI(
    title="Multi-Source Knowledge Agent",
    description="An AI agent that routes questions to multiple data sources: PostgreSQL, Pinecone Vector DB, and External APIs",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Internal APIs (used by AI tools)
app.include_router(orders.router, prefix="/internal", tags=["Internal"])
app.include_router(revenue.router, prefix="/internal", tags=["Internal"])
app.include_router(utils.router, prefix="/internal", tags=["Internal"])

# Agent API (main entry point)
app.include_router(agent.router, prefix="/agent", tags=["Agent"])

# Data API (view available data sources)
app.include_router(data.router, prefix="/data", tags=["Data"])


@app.get("/", tags=["Health"])
def root():
    return {
        "name": "Multi-Source Knowledge Agent",
        "status": "running",
        "endpoints": {
            "ask": "/agent/ask",
            "sources": "/agent/sources",
            "docs": "/docs",
        },
    }
