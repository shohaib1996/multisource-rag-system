from fastapi import APIRouter
from pydantic import BaseModel
from app.ai.router import route_question, DATA_SOURCES

router = APIRouter()


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    question: str
    answer: str
    available_sources: dict


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask the Multi-Source Knowledge Agent",
    description="Routes your question to the appropriate data source (database, documents, or external APIs) and returns an answer.",
)
def ask_agent(request: AskRequest):
    """
    Main endpoint for the Multi-Source Knowledge Agent.

    Supported question types:
    - ORDER: "What is the status of order 123?"
    - REVENUE: "What was our revenue last month?"
    - CURRENCY: "Convert 100 USD to EUR"
    - EXCHANGE: "What is the exchange rate from USD to JPY?"
    - DOCS: "What is the refund policy?"
    """
    answer = route_question(request.question)

    return {
        "question": request.question,
        "answer": answer,
        "available_sources": DATA_SOURCES
    }


@router.get(
    "/sources",
    summary="List available data sources",
    description="Returns all data sources available to the knowledge agent.",
)
def list_sources():
    """List all data sources the agent can query."""
    return {
        "sources": DATA_SOURCES,
        "total": len(DATA_SOURCES)
    }
