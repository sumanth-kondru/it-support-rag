"""
IT Support RAG Chatbot
- Built with LangChain + Ollama (local LLM, no API key needed)
- Vector store: ChromaDB
- API: FastAPI (same concept as Spring Boot REST APIs)
- Monitoring: Prometheus metrics endpoint
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time
import os
import logging

# ── Logging setup (same as any app you've deployed) ─────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── FastAPI app (same concept as Spring Boot @RestController) ────────────────
app = FastAPI(
    title="IT Support RAG Chatbot",
    description="AI-powered IT helpdesk using local LLM — no data leaves your network",
    version="1.0.0"
)

# Allow frontend to call this API (like CORS config in Spring Boot)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ── Prometheus metrics (you already know Prometheus!) ────────────────────────
questions_total   = Counter("itsupport_questions_total",   "Total questions asked")
questions_success = Counter("itsupport_questions_success",  "Successful answers")
questions_failed  = Counter("itsupport_questions_failed",   "Failed questions")
response_time     = Histogram("itsupport_response_seconds", "Response time in seconds")
active_sessions   = Counter("itsupport_sessions_total",     "Total chat sessions started")

# ── Request / Response models (same as Spring Boot @RequestBody) ─────────────
class Question(BaseModel):
    text: str
    session_id: str = "default"

class Answer(BaseModel):
    question: str
    answer: str
    sources: list[str]
    response_time_seconds: float

class HealthResponse(BaseModel):
    status: str
    model: str
    documents_loaded: int
    vector_store_ready: bool

# ── Global state (loaded once at startup, like Spring Boot @PostConstruct) ───
qa_chain = None
doc_count = 0

# ── Build the RAG pipeline ───────────────────────────────────────────────────
def build_rag_pipeline():
    """
    This is the core RAG pipeline:
    1. Load IT support documents
    2. Split into chunks
    3. Store in ChromaDB vector store
    4. Connect to local Ollama LLM
    5. Return a Q&A chain
    """
    global doc_count

    logger.info("🔧 Building RAG pipeline...")

    # Step 1: LOAD documents (like reading config files in DevOps)
    logger.info("📄 Loading IT support documents...")
    loader = DirectoryLoader(
        "docs/",
        glob="**/*.txt",
        loader_cls=TextLoader
    )
    documents = loader.load()
    doc_count = len(documents)
    logger.info(f"✅ Loaded {doc_count} documents")

    # Step 2: CHUNK — split into smaller pieces
    # Why? LLMs have context limits (like memory limits in K8s pods)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,      # 500 chars per chunk
        chunk_overlap=50     # 50 char overlap to preserve context
    )
    chunks = splitter.split_documents(documents)
    logger.info(f"✅ Split into {len(chunks)} chunks")

    # Step 3: EMBED + STORE in ChromaDB
    # Ollama runs locally — no API key, no data sent externally
    logger.info("🧠 Creating embeddings with Ollama (local, free)...")
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text",  # free embedding model
        base_url="http://localhost:11434"
    )
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="./chroma_db"  # saved to disk like a database
    )
    logger.info("✅ Vector store created")

    # Step 4: Define the prompt template
    # This tells the LLM HOW to answer — prompt engineering!
    prompt_template = """You are an expert IT support engineer helping users solve technical problems.
Use the following IT support documentation to answer the question.
If you don't know the answer from the documentation, say "I don't have documentation for this issue. Please contact the IT helpdesk directly."
Always be helpful, clear, and professional.

IT Support Documentation:
{context}

User Question: {question}

IT Support Answer:"""

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )

    # Step 5: Connect to local Ollama LLM
    logger.info("🤖 Connecting to Ollama LLM...")
    llm = Ollama(
        model="llama3.2",           # free, runs locally on your Mac
        base_url="http://localhost:11434",
        temperature=0.1             # low = factual answers (good for IT support)
    )

    # Step 6: BUILD the RAG chain
    # RetrievalQA = Search docs first → then answer using LLM
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(
            search_kwargs={"k": 3}   # retrieve top 3 most relevant chunks
        ),
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True
    )

    logger.info("✅ RAG pipeline ready!")
    return chain


# ── Startup event (like Spring Boot @PostConstruct) ──────────────────────────
@app.on_event("startup")
async def startup():
    global qa_chain
    logger.info("🚀 IT Support Chatbot starting up...")
    qa_chain = build_rag_pipeline()
    logger.info("✅ Application ready to serve requests")


# ── API ENDPOINTS (same concept as Spring Boot @RestController) ──────────────

# POST /ask — main endpoint (like @PostMapping in Spring Boot)
@app.post("/ask", response_model=Answer)
async def ask_question(question: Question):
    """Ask the IT support chatbot a question"""

    if not qa_chain:
        raise HTTPException(status_code=503, detail="RAG pipeline not ready yet")

    # Prometheus counter — you already know this!
    questions_total.inc()
    start_time = time.time()

    try:
        logger.info(f"❓ Question received: {question.text}")

        # This is where RAG magic happens:
        # 1. Search ChromaDB for relevant IT docs
        # 2. Feed docs + question to local LLM
        # 3. Get answer back
        result = qa_chain({"query": question.text})

        duration = time.time() - start_time
        response_time.observe(duration)
        questions_success.inc()

        # Extract source document names
        sources = []
        if "source_documents" in result:
            sources = list(set([
                doc.metadata.get("source", "unknown").split("/")[-1]
                for doc in result["source_documents"]
            ]))

        logger.info(f"✅ Answered in {duration:.2f}s from sources: {sources}")

        # Return JSON response (like ResponseEntity.ok() in Spring Boot)
        return Answer(
            question=question.text,
            answer=result["result"],
            sources=sources,
            response_time_seconds=round(duration, 2)
        )

    except Exception as e:
        questions_failed.inc()
        logger.error(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# GET /health — K8s liveness probe hits this (like Spring Actuator /health)
@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint — K8s liveness and readiness probe"""
    return HealthResponse(
        status="healthy",
        model="llama3.2 (local)",
        documents_loaded=doc_count,
        vector_store_ready=qa_chain is not None
    )


# GET /metrics — Prometheus scrapes this (you already configure this in K8s!)
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint — Grafana reads this"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# GET / — Simple welcome (useful for testing)
@app.get("/")
async def root():
    return {
        "app": "IT Support RAG Chatbot",
        "model": "Llama 3.2 (local, free, private)",
        "status": "running",
        "endpoints": {
            "ask": "POST /ask",
            "health": "GET /health",
            "metrics": "GET /metrics",
            "docs": "GET /docs"   # FastAPI auto-generates Swagger like Spring Boot!
        }
    }
