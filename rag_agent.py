import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

os.environ.setdefault("USER_AGENT", "AccessBankGhanaBot/1.0")

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain.tools import tool
from langchain.agents import create_agent
from scraper import load_website_data

load_dotenv()

print("🏦 Initializing Access Bank Ghana AI Assistant...")

# ── Models ─────────────────────────────────────────────────────────────────
model = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_store = InMemoryVectorStore(embeddings)

# ── Load & Index Website ───────────────────────────────────────────────────
splits = load_website_data()
vector_store.add_documents(documents=splits)
print(f"✅ Indexed {len(splits)} chunks from Access Bank Ghana website!")

# ── RAG Tool ───────────────────────────────────────────────────────────────
@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve detailed information from Access Bank Ghana website and official knowledge base to answer queries accurately."""
    retrieved_docs = vector_store.similarity_search(query, k=6)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata.get('source', 'Bank Records')}\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs

# ── Agent ──────────────────────────────────────────────────────────────────
tools = [retrieve_context]
prompt = (
    "You are the official AI Customer Service Assistant for Access Bank Ghana. "
    "You provide clear, accurate, and up-to-date banking information regarding accounts, "
    "loans, interest rates, cards, digital banking (*901#, Access More app), and branch services. "
    "Always check the retrieval tool for accurate and up-to-date facts before answering. "
    "Always format your answers neatly for WhatsApp (use bullet points and bold headers where appropriate). "
    "Be polite, concise, professional, and helpful. "
    "If a specific figure, tariff, or fee is not explicitly found in the retrieved context, "
    "do not guess; politely direct the customer to contact Access Bank Ghana Customer Care at 0800 004 400 "
    "or visit any Access Bank Ghana branch."
)
agent = create_agent(model, tools, system_prompt=prompt)
print("✅ Access Bank Ghana AI Assistant is ready!")