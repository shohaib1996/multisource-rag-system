import os
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

load_dotenv()

INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# 1. Initialize Pinecone
pc = Pinecone()
index = pc.Index(INDEX_NAME)

# 2. Embeddings
embeddings = OpenAIEmbeddings()

# 3. LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=100)


def ask(question: str):
    # Embed question
    query_vector = embeddings.embed_query(question)

    # Search Pinecone
    results = index.query(vector=query_vector, top_k=3, include_metadata=True)

    # Combine context
    context = "\n\n".join(match["metadata"]["text"] for match in results["matches"])

    # Ask LLM
    prompt = f"""
Answer the question using ONLY the context below.
If the answer is not in the context, say "I don't know".

Context:
{context}

Question:
{question}
"""

    response = llm.invoke(prompt)
    return response.content


if __name__ == "__main__":
    print(ask("How long does shipping take?"))
