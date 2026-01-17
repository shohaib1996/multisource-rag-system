import re
import json
from langchain_openai import ChatOpenAI
from app.ai.tools.order_tool import get_order_status
from app.ai.tools.revenue_tool import get_revenue_summary
from app.ai.tools.currency_tool import convert_currency
from app.ai.tools.exchange_rate_tool import convert_with_live_rate
from app.knowledge.query import ask as ask_docs

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Data sources registry for visibility
DATA_SOURCES = {
    "ORDER": "PostgreSQL Database (orders table)",
    "REVENUE": "PostgreSQL Database (payments table)",
    "CURRENCY": "Internal API (mock rates) with External API fallback",
    "EXCHANGE": "External API (frankfurter.app - live rates)",
    "DOCS": "Pinecone Vector DB (knowledge base documents)",
}

# Handler mapping
HANDLERS = {
    "ORDER": lambda q: handle_order(q),
    "REVENUE": lambda q: handle_revenue(q),
    "CURRENCY": lambda q: handle_currency(q),
    "EXCHANGE": lambda q: handle_exchange_rate(q),
    "DOCS": lambda q: handle_docs(q),
}


def detect_intents(question: str) -> list[dict]:
    """
    Detect multiple intents in a single question.
    Returns a list of intents with their relevant sub-questions.
    """
    detect_prompt = f"""
Analyze this question and identify ALL intents present.

Available intent types:
- ORDER: questions about order status, order tracking (needs order ID)
- REVENUE: questions about revenue, sales, payments for a time period
- CURRENCY: questions about converting specific amounts between currencies
- EXCHANGE: questions about current exchange rates
- DOCS: questions about policies, shipping, returns, refunds, FAQ, terms

Return a JSON array of objects, each with "intent" and "sub_question" fields.
Extract the relevant part of the question for each intent.

Question: {question}

Examples:

Input: "What is the status of order 5 and what's the refund policy?"
Output: [{{"intent": "ORDER", "sub_question": "What is the status of order 5?"}}, {{"intent": "DOCS", "sub_question": "What's the refund policy?"}}]

Input: "Convert 100 USD to EUR"
Output: [{{"intent": "CURRENCY", "sub_question": "Convert 100 USD to EUR"}}]

Input: "Show me order 3 status, revenue for January, and shipping policy"
Output: [{{"intent": "ORDER", "sub_question": "Show me order 3 status"}}, {{"intent": "REVENUE", "sub_question": "revenue for January"}}, {{"intent": "DOCS", "sub_question": "shipping policy"}}]

Return ONLY the JSON array, no other text.
"""
    response = llm.invoke(detect_prompt).content.strip()

    # Clean up response - remove markdown code blocks if present
    if response.startswith("```"):
        response = response.split("```")[1]
        if response.startswith("json"):
            response = response[4:]
    response = response.strip()

    try:
        intents = json.loads(response)
        return intents
    except json.JSONDecodeError:
        # Fallback: treat as single intent
        return [{"intent": "DOCS", "sub_question": question}]


def route_question(question: str) -> str:
    """
    Route user questions to appropriate data sources.
    Supports multi-intent queries (e.g., "Order 1 status AND refund policy").
    """
    # Detect all intents in the question
    intents = detect_intents(question)

    # Single intent - simple response
    if len(intents) == 1:
        intent = intents[0]["intent"].upper()
        sub_question = intents[0]["sub_question"]
        handler = HANDLERS.get(intent, HANDLERS["DOCS"])
        result = handler(sub_question)
        source = DATA_SOURCES.get(intent, DATA_SOURCES["DOCS"])
        return f"[Source: {source}]\n\n{result}"

    # Multiple intents - parallel processing
    results = []
    for i, item in enumerate(intents, 1):
        intent = item["intent"].upper()
        sub_question = item["sub_question"]
        handler = HANDLERS.get(intent, HANDLERS["DOCS"])
        source = DATA_SOURCES.get(intent, DATA_SOURCES["DOCS"])

        try:
            result = handler(sub_question)
        except Exception as e:
            result = f"Error: {str(e)}"

        results.append(f"**[{i}] {intent}**\n[Source: {source}]\n{result}")

    return "\n\n---\n\n".join(results)


def handle_order(question: str) -> str:
    """Extract order ID and fetch order status."""
    match = re.search(r'\b(\d+)\b', question)
    if not match:
        return "I couldn't find an order ID in your question. Please provide an order ID."

    order_id = int(match.group(1))
    data = get_order_status.invoke({"order_id": order_id})
    return f"Order #{order_id} details: {data}"


def handle_revenue(question: str) -> str:
    """Extract date range and fetch revenue summary."""
    extract_prompt = f"""
Extract the date range from this question.
Return ONLY in this exact format: START_DATE,END_DATE
Use YYYY-MM-DD format.
If no specific dates mentioned, use last 30 days from today (2025-01-15).

Question: {question}

Example outputs:
2025-01-01,2025-01-15
2024-12-01,2024-12-31
"""
    dates = llm.invoke(extract_prompt).content.strip()

    try:
        start_date, end_date = dates.split(",")
        data = get_revenue_summary.invoke({
            "start_date": start_date.strip(),
            "end_date": end_date.strip()
        })
        return f"Revenue summary from {start_date} to {end_date}: {data}"
    except Exception as e:
        return f"Error processing revenue query: {str(e)}"


def handle_currency(question: str) -> str:
    """Extract currency conversion parameters and use live rates."""
    extract_prompt = f"""
Extract currency conversion details from this question.
Return ONLY in this exact format: AMOUNT,FROM_CURRENCY,TO_CURRENCY

Question: {question}

Example outputs:
100,USD,BDT
50,USD,EUR
"""
    params = llm.invoke(extract_prompt).content.strip()

    try:
        parts = params.split(",")
        amount = float(parts[0].strip())
        from_curr = parts[1].strip().upper()
        to_curr = parts[2].strip().upper()

        # Try live rates first (external API)
        data = convert_with_live_rate.invoke({
            "amount": amount,
            "from_currency": from_curr,
            "to_currency": to_curr
        })

        # If live API failed, fallback to internal mock rates
        if "error" in data:
            data = convert_currency.invoke({
                "amount": amount,
                "from_currency": from_curr,
                "to_currency": to_curr
            })
            data["source"] = "internal (fallback)"

        return f"Currency conversion: {data}"
    except Exception as e:
        return f"Error processing currency conversion: {str(e)}"


def handle_exchange_rate(question: str) -> str:
    """Get current exchange rate between two currencies."""
    extract_prompt = f"""
Extract the two currencies from this exchange rate question.
Return ONLY in this exact format: FROM_CURRENCY,TO_CURRENCY

Question: {question}

Example outputs:
USD,EUR
GBP,JPY
"""
    params = llm.invoke(extract_prompt).content.strip()

    try:
        parts = params.split(",")
        from_curr = parts[0].strip().upper()
        to_curr = parts[1].strip().upper()

        from app.ai.tools.exchange_rate_tool import get_live_exchange_rate
        data = get_live_exchange_rate.invoke({
            "from_currency": from_curr,
            "to_currency": to_curr
        })

        if "error" not in data:
            return f"Current exchange rate: 1 {from_curr} = {data['rate']} {to_curr} (as of {data['date']})"
        return f"Exchange rate lookup failed: {data['error']}"
    except Exception as e:
        return f"Error fetching exchange rate: {str(e)}"


def handle_docs(question: str) -> str:
    """Query the knowledge base documents."""
    return ask_docs(question)


if __name__ == "__main__":
    print("=== SINGLE INTENT: ORDER ===")
    print(route_question("What is the status of order 1?"))

    print("\n" + "="*50 + "\n")

    print("=== SINGLE INTENT: DOCS ===")
    print(route_question("What is the refund policy?"))

    print("\n" + "="*50 + "\n")

    print("=== MULTI-INTENT: ORDER + DOCS ===")
    print(route_question("What is the status of order 1 and what's the refund policy?"))

    print("\n" + "="*50 + "\n")

    print("=== MULTI-INTENT: CURRENCY + EXCHANGE + DOCS ===")
    print(route_question("Convert 50 USD to EUR, what's the USD to JPY rate, and show shipping policy"))
