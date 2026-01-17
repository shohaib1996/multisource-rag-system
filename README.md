# Multi-Source Knowledge Agent

An AI-powered knowledge agent that intelligently routes questions to multiple data sources and returns unified answers. Built with FastAPI, LangChain, and GPT-4o-mini.

## Architecture

```
                         ┌─────────────────────┐
                         │   User Question     │
                         └──────────┬──────────┘
                                    │
                         ┌──────────▼──────────┐
                         │   POST /agent/ask   │
                         └──────────┬──────────┘
                                    │
                         ┌──────────▼──────────┐
                         │  Intent Detection   │
                         │  (LLM-based router) │
                         └──────────┬──────────┘
                                    │
          ┌─────────────┬───────────┼───────────┬─────────────┐
          │             │           │           │             │
          ▼             ▼           ▼           ▼             ▼
    ┌──────────┐  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
    │  ORDER   │  │ REVENUE  │ │ CURRENCY │ │ EXCHANGE │ │   DOCS   │
    └────┬─────┘  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
         │             │           │             │             │
         ▼             ▼           ▼             ▼             ▼
    ┌──────────┐  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
    │PostgreSQL│  │PostgreSQL│ │ Internal │ │ External │ │ Pinecone │
    │ (orders) │  │(payments)│ │   API    │ │   API    │ │ VectorDB │
    └──────────┘  └──────────┘ └────┬─────┘ └──────────┘ └──────────┘
                                    │
                               ┌────▼─────┐
                               │ Fallback │
                               │ to Live  │
                               │   API    │
                               └──────────┘
```

## Features

- **Multi-Source Routing**: Automatically routes questions to the appropriate data source
- **Multi-Intent Queries**: Handles compound questions like "What's order 1 status AND the refund policy?"
- **5 Data Sources**:
  - PostgreSQL (orders, revenue)
  - Pinecone Vector DB (knowledge base documents)
  - Internal APIs (mock currency rates)
  - External APIs (live exchange rates from frankfurter.app)
- **Fallback Logic**: Gracefully falls back to alternative sources on failure
- **RAG Pipeline**: Retrieval-Augmented Generation for document Q&A

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI |
| LLM | OpenAI GPT-4o-mini |
| Orchestration | LangChain |
| Vector DB | Pinecone |
| Database | PostgreSQL (Neon) |
| External API | frankfurter.app |

## Project Structure

```
multisource-rag/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── db.py                   # Database connection
│   ├── routers/
│   │   ├── agent.py            # /agent/ask endpoint
│   │   ├── orders.py           # Order status API
│   │   ├── revenue.py          # Revenue summary API
│   │   └── utils.py            # Currency conversion API
│   ├── ai/
│   │   ├── router.py           # Intent detection & routing
│   │   └── tools/
│   │       ├── order_tool.py   # Order lookup tool
│   │       ├── revenue_tool.py # Revenue query tool
│   │       ├── currency_tool.py# Currency conversion tool
│   │       └── exchange_rate_tool.py # Live rates tool
│   └── knowledge/
│       ├── ingest.py           # Document ingestion to Pinecone
│       └── query.py            # RAG query pipeline
├── knowledge_base/             # Source documents
│   ├── shipping_policy.txt
│   ├── refund_policy.txt
│   ├── warranty_policy.txt
│   ├── faq.txt
│   └── terms.txt
├── tables.sql                  # Database schema
├── requirements.txt
└── README.md
```

## Setup

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd multisource-rag
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file:

```env
OPENAI_API_KEY=your_openai_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=ecommerce-knowledge
DATABASE_URL=postgresql://user:pass@host/dbname
```

### 3. Setup database

Run the SQL schema in `tables.sql` against your PostgreSQL database.

### 4. Ingest documents to Pinecone

```bash
python -m app.knowledge.ingest
```

### 5. Run the server

```bash
uvicorn app.main:app --reload
```

## API Usage

### Ask a Question

```bash
POST /agent/ask
Content-Type: application/json

{
  "question": "What is the status of order 1?"
}
```

### Example Queries

| Query Type | Example |
|------------|---------|
| Order Status | "What is the status of order 5?" |
| Revenue | "What was our revenue in January 2025?" |
| Currency | "Convert 100 USD to EUR" |
| Exchange Rate | "What is the USD to JPY exchange rate?" |
| Documents | "What is the refund policy?" |
| Multi-Intent | "Show order 1 status and the shipping policy" |

### List Data Sources

```bash
GET /agent/sources
```

### Interactive Docs

Visit `http://localhost:8000/docs` for Swagger UI.

## Example Response

**Single Intent:**
```json
{
  "question": "What is the refund policy?",
  "answer": "[Source: Pinecone Vector DB (knowledge base documents)]\n\nRefunds are processed within 5-7 business days...",
  "available_sources": {
    "ORDER": "PostgreSQL Database (orders table)",
    "REVENUE": "PostgreSQL Database (payments table)",
    "CURRENCY": "Internal API with External API fallback",
    "EXCHANGE": "External API (frankfurter.app)",
    "DOCS": "Pinecone Vector DB (knowledge base documents)"
  }
}
```

**Multi-Intent:**
```json
{
  "question": "What is order 1 status and the refund policy?",
  "answer": "**[1] ORDER**\n[Source: PostgreSQL Database]\nOrder #1 details: {...}\n\n---\n\n**[2] DOCS**\n[Source: Pinecone Vector DB]\nRefunds are processed within...",
  "available_sources": {...}
}
```

## Key Concepts Demonstrated

1. **LLM-Based Routing** - Using GPT to classify and route queries
2. **Multi-Source RAG** - Combining vector search with structured data
3. **Tool Abstraction** - LangChain tools wrapping APIs
4. **Fallback Patterns** - Graceful degradation when sources fail
5. **Intent Detection** - Parsing compound queries into multiple intents

## License

MIT
