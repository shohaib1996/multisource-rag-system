import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# 1. Load documents
docs = []
docs_path = "knowledge_base"

for file in os.listdir(docs_path):
    if file.endswith(".txt"):
        loader = TextLoader(os.path.join(docs_path, file))
        docs.extend(loader.load())

# 2. Split documents
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(docs)

# 3. Create embeddings
embeddings = OpenAIEmbeddings()

# 4. Store in Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

vectors = []
for i, chunk in enumerate(chunks):
    vector = embeddings.embed_query(chunk.page_content)
    vectors.append((f"doc-{i}", vector, {"text": chunk.page_content}))

index.upsert(vectors)

print(f"✅ Ingested {len(vectors)} chunks into Pinecone")
