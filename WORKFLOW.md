# Workflow Guide

This document explains how the Multi-Source Knowledge Agent works with real examples.

---

## How It Works

```
User Question → Intent Detection → Route to Source(s) → Fetch Data → Return Answer
```

The agent uses an LLM to understand what you're asking, then automatically picks the right data source(s) to answer your question.

---

## User Story: E-Commerce Support Agent

Imagine you're a customer support agent at an e-commerce company. Instead of switching between multiple dashboards, you ask one AI agent that queries everything for you.

---

## Example 1: Simple Order Lookup

**User asks:**
> "What is the status of order 42?"

**Behind the scenes:**

```
Step 1: Intent Detection
┌─────────────────────────────────────────────────────────┐
│ LLM analyzes: "What is the status of order 42?"         │
│ Detected intent: ORDER                                  │
│ Extracted: order_id = 42                                │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
Step 2: Route to Handler
┌─────────────────────────────────────────────────────────┐
│ Router selects: handle_order()                          │
│ Data source: PostgreSQL (orders table)                  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
Step 3: Execute Tool
┌─────────────────────────────────────────────────────────┐
│ Tool: get_order_status(order_id=42)                     │
│ API call: GET /internal/orders/42                       │
│ SQL: SELECT * FROM orders WHERE id = 42                 │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
Step 4: Return Response
┌─────────────────────────────────────────────────────────┐
│ [Source: PostgreSQL Database (orders table)]            │
│                                                         │
│ Order #42 details: {                                    │
│   "id": 42,                                             │
│   "status": "shipped",                                  │
│   "total_amount": 150.00,                               │
│   "currency": "USD",                                    │
│   "created_at": "2025-01-10T14:30:00"                   │
│ }                                                       │
└─────────────────────────────────────────────────────────┘
```

---

## Example 2: Policy Question (RAG)

**User asks:**
> "Can I return a product after 30 days?"

**Behind the scenes:**

```
Step 1: Intent Detection
┌─────────────────────────────────────────────────────────┐
│ LLM analyzes: "Can I return a product after 30 days?"   │
│ Detected intent: DOCS                                   │
│ Topic: return policy                                    │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
Step 2: Route to Handler
┌─────────────────────────────────────────────────────────┐
│ Router selects: handle_docs()                           │
│ Data source: Pinecone Vector DB                         │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
Step 3: RAG Pipeline
┌─────────────────────────────────────────────────────────┐
│ 1. Embed question using OpenAI embeddings               │
│ 2. Search Pinecone for similar chunks (top_k=3)         │
│ 3. Retrieved chunks from refund_policy.txt:             │
│    - "Returns accepted within 14 days of delivery..."   │
│    - "Items must be unused and in original packaging.." │
│    - "Refunds processed within 5-7 business days..."    │
│ 4. Send context + question to LLM                       │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
Step 4: Return Response
┌─────────────────────────────────────────────────────────┐
│ [Source: Pinecone Vector DB (knowledge base documents)] │
│                                                         │
│ Based on our refund policy, returns are only accepted   │
│ within 14 days of delivery. Unfortunately, a product    │
│ cannot be returned after 30 days.                       │
└─────────────────────────────────────────────────────────┘
```

---

## Example 3: Live Currency Conversion

**User asks:**
> "Convert 500 USD to EUR"

**Behind the scenes:**

```
Step 1: Intent Detection
┌─────────────────────────────────────────────────────────┐
│ LLM analyzes: "Convert 500 USD to EUR"                  │
│ Detected intent: CURRENCY                               │
│ Extracted: amount=500, from=USD, to=EUR                 │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
Step 2: Route to Handler
┌─────────────────────────────────────────────────────────┐
│ Router selects: handle_currency()                       │
│ Data source: External API (with internal fallback)      │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
Step 3: Execute Tool (with fallback)
┌─────────────────────────────────────────────────────────┐
│ Primary: convert_with_live_rate()                       │
│ API call: GET https://api.frankfurter.app/latest        │
│           ?amount=500&from=USD&to=EUR                   │
│                                                         │
│ If API fails → Fallback to internal mock rates          │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
Step 4: Return Response
┌─────────────────────────────────────────────────────────┐
│ [Source: External API (frankfurter.app - live rates)]   │
│                                                         │
│ Currency conversion: {                                  │
│   "amount": 500,                                        │
│   "from": "USD",                                        │
│   "to": "EUR",                                          │
│   "converted_amount": 460.50,                           │
│   "date": "2025-01-15",                                 │
│   "source": "frankfurter.app (live)"                    │
│ }                                                       │
└─────────────────────────────────────────────────────────┘
```

---

## Example 4: Multi-Intent Query (The Power Feature)

**User asks:**
> "What is the status of order 7, how much is 100 USD in EUR, and what's your shipping policy?"

**Behind the scenes:**

```
Step 1: Intent Detection (Multi-Intent)
┌─────────────────────────────────────────────────────────┐
│ LLM analyzes the compound question                      │
│ Detected intents:                                       │
│   1. ORDER → "What is the status of order 7"            │
│   2. CURRENCY → "how much is 100 USD in EUR"            │
│   3. DOCS → "what's your shipping policy"               │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
Step 2: Parallel Routing
┌─────────────────────────────────────────────────────────┐
│ Intent 1 → handle_order() → PostgreSQL                  │
│ Intent 2 → handle_currency() → External API             │
│ Intent 3 → handle_docs() → Pinecone                     │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
Step 3: Execute All Tools
┌─────────────────────────────────────────────────────────┐
│ Tool 1: get_order_status(order_id=7)                    │
│ Tool 2: convert_with_live_rate(100, USD, EUR)           │
│ Tool 3: RAG search for "shipping policy"                │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
Step 4: Combined Response
┌─────────────────────────────────────────────────────────┐
│ **[1] ORDER**                                           │
│ [Source: PostgreSQL Database (orders table)]            │
│ Order #7 details: {                                     │
│   "status": "delivered",                                │
│   "total_amount": 89.99                                 │
│ }                                                       │
│                                                         │
│ ---                                                     │
│                                                         │
│ **[2] CURRENCY**                                        │
│ [Source: External API (frankfurter.app - live rates)]   │
│ Currency conversion: {                                  │
│   "amount": 100,                                        │
│   "converted_amount": 92.10,                            │
│   "from": "USD",                                        │
│   "to": "EUR"                                           │
│ }                                                       │
│                                                         │
│ ---                                                     │
│                                                         │
│ **[3] DOCS**                                            │
│ [Source: Pinecone Vector DB (knowledge base documents)] │
│ Standard shipping takes 5-7 business days. Express      │
│ shipping is available for an additional $15 and         │
│ delivers within 2-3 business days.                      │
└─────────────────────────────────────────────────────────┘
```

---

## Example 5: Revenue Query (Admin Use Case)

**User asks:**
> "What was our total revenue in December 2024?"

**Behind the scenes:**

```
Step 1: Intent Detection
┌─────────────────────────────────────────────────────────┐
│ LLM analyzes: "What was our total revenue in Dec 2024?" │
│ Detected intent: REVENUE                                │
│ Extracted dates: 2024-12-01 to 2024-12-31               │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
Step 2: Route to Handler
┌─────────────────────────────────────────────────────────┐
│ Router selects: handle_revenue()                        │
│ Data source: PostgreSQL (payments table)                │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
Step 3: Execute Tool
┌─────────────────────────────────────────────────────────┐
│ Tool: get_revenue_summary(                              │
│   start_date="2024-12-01",                              │
│   end_date="2024-12-31"                                 │
│ )                                                       │
│ SQL: SELECT SUM(amount), currency FROM payments         │
│      WHERE payment_status = 'paid'                      │
│      AND created_at BETWEEN '2024-12-01' AND '2024-12-31│
│      GROUP BY currency                                  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
Step 4: Return Response
┌─────────────────────────────────────────────────────────┐
│ [Source: PostgreSQL Database (payments table)]          │
│                                                         │
│ Revenue summary from 2024-12-01 to 2024-12-31: [        │
│   {"total_payments": 156, "total_revenue": 12450.00,    │
│    "currency": "USD"},                                  │
│   {"total_payments": 23, "total_revenue": 1820.50,      │
│    "currency": "EUR"}                                   │
│ ]                                                       │
└─────────────────────────────────────────────────────────┘
```

---

## Data Source Summary

| Intent | Source | What It Queries |
|--------|--------|-----------------|
| ORDER | PostgreSQL | `orders` table |
| REVENUE | PostgreSQL | `payments` table |
| CURRENCY | External API → Internal API | frankfurter.app (live) → mock rates (fallback) |
| EXCHANGE | External API | frankfurter.app |
| DOCS | Pinecone | Knowledge base documents via RAG |

---

## Fallback Flow

When the primary source fails, the system gracefully degrades:

```
User: "Convert 100 USD to BDT"
           │
           ▼
┌─────────────────────────┐
│ Try: frankfurter.app    │
│ Result: BDT not found   │
└───────────┬─────────────┘
            │ FAILED
            ▼
┌─────────────────────────┐
│ Fallback: Internal API  │
│ Mock rate: USD→BDT=120.5│
└───────────┬─────────────┘
            │ SUCCESS
            ▼
┌─────────────────────────┐
│ Response includes:      │
│ "source": "internal     │
│  (fallback)"            │
└─────────────────────────┘
```

---

## Try It Yourself

```bash
# Start the server
uvicorn app.main:app --reload

# Single intent
curl -X POST http://localhost:8000/agent/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the status of order 1?"}'

# Multi-intent
curl -X POST http://localhost:8000/agent/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Show order 5 status and the refund policy"}'

# Or use the Swagger UI
open http://localhost:8000/docs
```
