# File-by-File Query Flow

This document traces exactly how a query moves through your codebase, file by file.

---

## Quick Reference: File Responsibilities

| File | Purpose |
|------|---------|
| `app/main.py` | Entry point, registers all routers |
| `app/routers/agent.py` | Receives HTTP request at `/agent/ask` |
| `app/ai/router.py` | Brain - detects intent, routes to handlers |
| `app/ai/tools/*.py` | Tools that call internal/external APIs |
| `app/routers/orders.py` | Internal API for order data |
| `app/routers/revenue.py` | Internal API for revenue data |
| `app/routers/utils.py` | Internal API for currency (mock) |
| `app/knowledge/query.py` | RAG pipeline for document Q&A |
| `app/db.py` | Database connection |

---

## Flow 1: Order Status Query

**User asks:** `"What is the status of order 5?"`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: HTTP Request Arrives                                                │
│ File: app/main.py (lines 16)                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   app.include_router(agent.router, prefix="/agent", tags=["Agent"])         │
│                                                                             │
│   → Request: POST /agent/ask                                                │
│   → FastAPI routes to agent.router                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Agent Endpoint Receives Request                                     │
│ File: app/routers/agent.py (lines 20-35)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   @router.post("/ask")                                                      │
│   def ask_agent(request: AskRequest):                                       │
│       answer = route_question(request.question)  ← Calls router.py          │
│       return {                                                              │
│           "question": request.question,                                     │
│           "answer": answer,                                                 │
│           "available_sources": DATA_SOURCES                                 │
│       }                                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: Intent Detection                                                    │
│ File: app/ai/router.py (lines 31-78)                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   def detect_intents(question: str) -> list[dict]:                          │
│       detect_prompt = """                                                   │
│       Analyze this question and identify ALL intents...                     │
│       """                                                                   │
│       response = llm.invoke(detect_prompt)  ← Calls OpenAI GPT-4o-mini      │
│       intents = json.loads(response)                                        │
│       return intents                                                        │
│                                                                             │
│   Result: [{"intent": "ORDER", "sub_question": "status of order 5"}]        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: Route to Handler                                                    │
│ File: app/ai/router.py (lines 81-113)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   def route_question(question: str) -> str:                                 │
│       intents = detect_intents(question)                                    │
│                                                                             │
│       # Single intent detected                                              │
│       intent = intents[0]["intent"]  → "ORDER"                              │
│       handler = HANDLERS.get(intent)  → handle_order()                      │
│       result = handler(sub_question)                                        │
│                                                                             │
│   HANDLERS dict (lines 22-28):                                              │
│   {                                                                         │
│       "ORDER": lambda q: handle_order(q),      ← Selected                   │
│       "REVENUE": lambda q: handle_revenue(q),                               │
│       "CURRENCY": lambda q: handle_currency(q),                             │
│       "EXCHANGE": lambda q: handle_exchange_rate(q),                        │
│       "DOCS": lambda q: handle_docs(q),                                     │
│   }                                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: Handle Order                                                        │
│ File: app/ai/router.py (lines 116-124)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   def handle_order(question: str) -> str:                                   │
│       match = re.search(r'\b(\d+)\b', question)  → Extracts "5"             │
│       order_id = int(match.group(1))  → 5                                   │
│                                                                             │
│       data = get_order_status.invoke({"order_id": order_id})                │
│               ↑                                                             │
│               └── Calls the LangChain tool                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 6: Execute Order Tool                                                  │
│ File: app/ai/tools/order_tool.py (lines 7-14)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   INTERNAL_API_BASE = "http://127.0.0.1:8000/internal"                      │
│                                                                             │
│   @tool                                                                     │
│   def get_order_status(order_id: int) -> dict:                              │
│       response = requests.get(f"{INTERNAL_API_BASE}/orders/{order_id}")     │
│       return response.json()                                                │
│                                                                             │
│   → Makes HTTP call to: GET /internal/orders/5                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 7: Internal Orders API                                                 │
│ File: app/routers/orders.py (lines 10-27)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   @router.get("/orders/{order_id}")                                         │
│   def get_order(order_id: int, db: Session = Depends(get_db)):              │
│       query = text("""                                                      │
│           SELECT id, status, total_amount, currency, created_at             │
│           FROM orders                                                       │
│           WHERE id = :order_id                                              │
│       """)                                                                  │
│       result = db.execute(query, {"order_id": order_id}).fetchone()         │
│       return dict(result._mapping)                                          │
│                                                                             │
│   → Queries PostgreSQL database                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 8: Database Connection                                                 │
│ File: app/db.py (lines 14-19)                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   DATABASE_URL = os.getenv("DATABASE_URL")  → PostgreSQL on Neon            │
│   engine = create_engine(DATABASE_URL)                                      │
│                                                                             │
│   def get_db():                                                             │
│       db = SessionLocal()                                                   │
│       try:                                                                  │
│           yield db  ← Provides DB session to orders.py                      │
│       finally:                                                              │
│           db.close()                                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 9: Response Bubbles Back Up                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   db.py          → Returns: Row(id=5, status="shipped", ...)                │
│        ↓                                                                    │
│   orders.py      → Returns: {"id": 5, "status": "shipped", ...}             │
│        ↓                                                                    │
│   order_tool.py  → Returns: {"id": 5, "status": "shipped", ...}             │
│        ↓                                                                    │
│   router.py      → Returns: "Order #5 details: {...}"                       │
│        ↓                                                                    │
│   agent.py       → Returns: {"question": "...", "answer": "...", ...}       │
│        ↓                                                                    │
│   User           → Receives JSON response                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Flow 2: Document Query (RAG)

**User asks:** `"What is the refund policy?"`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1-4: Same as Flow 1                                                    │
│ Files: main.py → agent.py → router.py                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Intent detected: DOCS                                                     │
│   Handler selected: handle_docs()                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: Handle Docs                                                         │
│ File: app/ai/router.py (lines 227-229)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   def handle_docs(question: str) -> str:                                    │
│       return ask_docs(question)  ← Calls knowledge/query.py                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 6: RAG Query Pipeline                                                  │
│ File: app/knowledge/query.py (lines 21-44)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   def ask(question: str):                                                   │
│       # 1. Embed question                                                   │
│       query_vector = embeddings.embed_query(question)                       │
│                           ↑                                                 │
│                           └── Calls OpenAI Embeddings API                   │
│                                                                             │
│       # 2. Search Pinecone                                                  │
│       results = index.query(vector=query_vector, top_k=3)                   │
│                     ↑                                                       │
│                     └── Calls Pinecone Vector DB                            │
│                                                                             │
│       # 3. Combine context from matches                                     │
│       context = "\n\n".join(match["metadata"]["text"]                       │
│                             for match in results["matches"])                │
│                                                                             │
│       # 4. Ask LLM with context                                             │
│       prompt = f"""                                                         │
│       Answer using ONLY the context below.                                  │
│       Context: {context}                                                    │
│       Question: {question}                                                  │
│       """                                                                   │
│       response = llm.invoke(prompt)  ← Calls OpenAI GPT-4o-mini             │
│       return response.content                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ External Services Called:                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   1. OpenAI API (embeddings)                                                │
│      → Converts "What is the refund policy?" into a 1536-dim vector         │
│                                                                             │
│   2. Pinecone                                                               │
│      → Searches for similar vectors                                         │
│      → Returns chunks from knowledge_base/refund_policy.txt                 │
│                                                                             │
│   3. OpenAI API (chat completion)                                           │
│      → Generates answer based on retrieved context                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Flow 3: Currency Conversion (External API + Fallback)

**User asks:** `"Convert 100 USD to EUR"`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1-4: Same as Flow 1                                                    │
│ Files: main.py → agent.py → router.py                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   Intent detected: CURRENCY                                                 │
│   Handler selected: handle_currency()                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: Handle Currency                                                     │
│ File: app/ai/router.py (lines 154-192)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   def handle_currency(question: str) -> str:                                │
│       # Extract params using LLM                                            │
│       extract_prompt = "Extract: AMOUNT,FROM,TO"                            │
│       params = llm.invoke(extract_prompt)  → "100,USD,EUR"                  │
│                                                                             │
│       amount = 100                                                          │
│       from_curr = "USD"                                                     │
│       to_curr = "EUR"                                                       │
│                                                                             │
│       # Try live rates first                                                │
│       data = convert_with_live_rate.invoke({...})                           │
│                                                                             │
│       # If failed, fallback                                                 │
│       if "error" in data:                                                   │
│           data = convert_currency.invoke({...})  ← Internal API             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 6A: Try External API (Primary)                                         │
│ File: app/ai/tools/exchange_rate_tool.py (lines 37-68)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   @tool                                                                     │
│   def convert_with_live_rate(amount, from_currency, to_currency):           │
│       url = "https://api.frankfurter.app/latest"                            │
│       params = {"amount": 100, "from": "USD", "to": "EUR"}                  │
│       response = requests.get(url, params=params)                           │
│       return {                                                              │
│           "converted_amount": 92.10,                                        │
│           "source": "frankfurter.app (live)"                                │
│       }                                                                     │
│                                                                             │
│   → Calls external frankfurter.app API                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                          ┌─────────┴─────────┐
                          │                   │
                     SUCCESS               FAILED
                          │                   │
                          ▼                   ▼
┌─────────────────────────────┐   ┌─────────────────────────────┐
│ Return live rate            │   │ STEP 6B: Fallback           │
│ Source: frankfurter.app     │   │ File: app/ai/tools/         │
│                             │   │        currency_tool.py     │
└─────────────────────────────┘   ├─────────────────────────────┤
                                  │                             │
                                  │ @tool                       │
                                  │ def convert_currency(...):  │
                                  │   → Calls /internal/utils/  │
                                  │     convert-currency        │
                                  │                             │
                                  │ File: app/routers/utils.py  │
                                  │ → Uses MOCK_RATES dict      │
                                  │                             │
                                  └─────────────────────────────┘
```

---

## Flow 4: Multi-Intent Query

**User asks:** `"What is order 5 status and the refund policy?"`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: Intent Detection (Multi)                                            │
│ File: app/ai/router.py (lines 31-78)                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   detect_intents() returns:                                                 │
│   [                                                                         │
│     {"intent": "ORDER", "sub_question": "What is order 5 status"},          │
│     {"intent": "DOCS", "sub_question": "the refund policy"}                 │
│   ]                                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: Route Multiple Intents                                              │
│ File: app/ai/router.py (lines 98-113)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   # Multiple intents - process each                                         │
│   results = []                                                              │
│   for item in intents:                                                      │
│       handler = HANDLERS.get(item["intent"])                                │
│       result = handler(item["sub_question"])                                │
│       results.append(f"**[{i}] {intent}**\n{result}")                       │
│                                                                             │
│   return "\n\n---\n\n".join(results)                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
┌───────────────────────────────┐   ┌───────────────────────────────┐
│ Intent 1: ORDER               │   │ Intent 2: DOCS                │
│                               │   │                               │
│ handle_order()                │   │ handle_docs()                 │
│      ↓                        │   │      ↓                        │
│ order_tool.py                 │   │ query.py                      │
│      ↓                        │   │      ↓                        │
│ orders.py                     │   │ Pinecone + OpenAI             │
│      ↓                        │   │      ↓                        │
│ PostgreSQL                    │   │ RAG Response                  │
└───────────────────────────────┘   └───────────────────────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Combined Response                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   **[1] ORDER**                                                             │
│   [Source: PostgreSQL Database (orders table)]                              │
│   Order #5 details: {"status": "shipped", ...}                              │
│                                                                             │
│   ---                                                                       │
│                                                                             │
│   **[2] DOCS**                                                              │
│   [Source: Pinecone Vector DB (knowledge base documents)]                   │
│   Refunds are processed within 5-7 business days...                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## File Dependency Graph

```
app/main.py
    │
    ├── app/routers/agent.py ─────────────────┐
    │       │                                 │
    │       └── app/ai/router.py              │
    │               │                         │
    │               ├── app/ai/tools/         │
    │               │   ├── order_tool.py ────┼── app/routers/orders.py ── app/db.py
    │               │   ├── revenue_tool.py ──┼── app/routers/revenue.py ─ app/db.py
    │               │   ├── currency_tool.py ─┼── app/routers/utils.py
    │               │   └── exchange_rate_tool.py (external API)
    │               │                         │
    │               └── app/knowledge/query.py (Pinecone + OpenAI)
    │                                         │
    ├── app/routers/orders.py ────────────────┘
    ├── app/routers/revenue.py
    └── app/routers/utils.py
```

---

## Summary: Which File Does What

| File | When It's Called | What It Does |
|------|------------------|--------------|
| `main.py` | Server starts | Registers all routers |
| `agent.py` | POST /agent/ask | Receives request, returns response |
| `router.py` | Every question | Detects intent, routes to handler |
| `order_tool.py` | ORDER intent | Calls internal orders API |
| `revenue_tool.py` | REVENUE intent | Calls internal revenue API |
| `currency_tool.py` | CURRENCY fallback | Calls internal currency API |
| `exchange_rate_tool.py` | CURRENCY/EXCHANGE | Calls external frankfurter.app |
| `orders.py` | Tool calls it | Queries PostgreSQL orders table |
| `revenue.py` | Tool calls it | Queries PostgreSQL payments table |
| `utils.py` | Tool calls it | Returns mock exchange rates |
| `query.py` | DOCS intent | Runs RAG pipeline (Pinecone + OpenAI) |
| `db.py` | Any DB query | Provides database connection |
