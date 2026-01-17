from fastapi import FastAPI
from app.routers import orders, revenue, utils, agent

app = FastAPI(
    title="Multi-Source Knowledge Agent",
    description="An AI agent that routes questions to multiple data sources: PostgreSQL, Pinecone Vector DB, and External APIs",
    version="1.0.0"
)

# Internal APIs (used by AI tools)
app.include_router(orders.router, prefix="/internal", tags=["Internal"])
app.include_router(revenue.router, prefix="/internal", tags=["Internal"])
app.include_router(utils.router, prefix="/internal", tags=["Internal"])

# Agent API (main entry point)
app.include_router(agent.router, prefix="/agent", tags=["Agent"])


@app.get("/", tags=["Health"])
def root():
    return {
        "name": "Multi-Source Knowledge Agent",
        "status": "running",
        "endpoints": {
            "ask": "/agent/ask",
            "sources": "/agent/sources",
            "docs": "/docs"
        }
    }
