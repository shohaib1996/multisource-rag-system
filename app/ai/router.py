from langchain_openai import ChatOpenAI
from app.ai.tools.order_tool import get_order_status
from app.knowledge.query import ask as ask_docs

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def route_question(question: str) -> str:
    """
    Decide which data source to use: database or documents.
    """
    router_prompt = f"""
You are a router.

Classify the user's question into ONE category:
- ORDER: questions about order status, order id, payment
- DOCS: questions about policies, shipping, returns, FAQ

Respond with ONLY one word: ORDER or DOCS.

Question:
{question}
"""
    decision = llm.invoke(router_prompt).content.strip().upper()

    if decision == "ORDER":
        # very simple extraction for now
        order_id = int("".join(filter(str.isdigit, question)))
        data = get_order_status.run({"order_id": order_id})
        return f"Order data: {data}"

    else:
        return ask_docs(question)


if __name__ == "__main__":
    print(route_question("What is the status of order 1?"))
    print("----")
    print(route_question("How long does shipping take?"))
