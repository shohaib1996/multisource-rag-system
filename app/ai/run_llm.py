from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from app.ai.tools.order_tool import get_order_status

load_dotenv()

# 1. Create LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 2. Bind tools (this is the modern way)
llm_with_tools = llm.bind_tools([get_order_status])

if __name__ == "__main__":
    # 3. Ask a natural language question
    response = llm_with_tools.invoke("What is the status of order 1?")

    print(response)
