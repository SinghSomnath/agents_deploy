# LangGraph PDF WebCrawl Router Agent

[![Python](https://img.shields.io/badge/Python-3.13.1-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3.27-1C3C3C.svg)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.6.7-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A FastAPI-powered intelligent routing agent that combines **PDF document ingestion** into AstraDB vector store with **live web crawling** capabilities. The agent automatically decides whether to answer questions from your uploaded documents or by searching and crawling the web in real-time.

## 🌟 Features

### 🤖 Intelligent Routing
- **LangGraph-based state machine** for decision making
- Automatic routing between:
  - **AstraDB**: Domain-specific documents (PDFs, company docs, technical manuals)
  - **Web Crawl**: Live web search via DuckDuckGo + page scraping
- Context-aware routing logic that considers uploaded documents

### 📄 PDF Document Processing
- Upload and ingest PDF files into AstraDB vector database
- Automatic text extraction using **pypdf**
- Intelligent chunking with overlap using **RecursiveCharacterTextSplitter**
- SHA-256 fingerprinting to prevent duplicate uploads
- Page-level metadata tracking

### 🌐 Web Crawling
- DuckDuckGo search integration for current information
- Smart HTML parsing with BeautifulSoup (extracts main content)
- Blocked domain filtering (social media, video sites)
- Retry logic with multiple query strategies
- User-agent rotation and timeout handling

### 🔍 Vector Search
- **AstraDB** as vector store backend
- **OpenRouter API** for embeddings (Qwen 8B by default)
- Configurable similarity search (top-k retrieval)
- Source attribution with file names and page numbers

### 🚀 RESTful API
- **FastAPI** framework with automatic OpenAPI docs
- Swagger UI at `/docs`
- Four main endpoints: `/upload`, `/ask`, `/documents`, `/health`
- Comprehensive request/response models with Pydantic
- Global exception handling

## 📋 Table of Contents

- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Environment Configuration](#-environment-configuration)
- [Usage](#-usage)
  - [Running the API Server](#running-the-api-server)
  - [Populating Sample Data](#populating-sample-data)
  - [API Endpoints](#api-endpoints)
- [Architecture](#-architecture)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

## 🔧 Prerequisites

- **Python 3.13.1** or higher
- **AstraDB Account** (free tier available at [astra.datastax.com](https://astra.datastax.com))
- **OpenRouter API Key** (get one at [openrouter.ai](https://openrouter.ai))
- Virtual environment (recommended)

## 📦 Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd agents_deploy
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Key Dependencies:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `langgraph` - State machine orchestration
- `langchain-astradb` - AstraDB vector store integration
- `langchain-openai` - OpenAI-compatible API wrapper
- `duckduckgo-search` - Web search API
- `beautifulsoup4` - HTML parsing
- `pypdf` - PDF text extraction
- `python-dotenv` - Environment variable management

## ⚙️ Environment Configuration

### 1. Create `.env` File

Create a `.env` file in the project root:

```bash
# OpenRouter API (for LLM and Embeddings)
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=qwen/qwen3-embedding-8b
OPENROUTER_MODEL_DIMENSIONS=4096

# AstraDB Configuration
ASTRA_DB_API_ENDPOINT=https://your-database-id-region.apps.astra.datastax.com
ASTRA_DB_APPLICATION_TOKEN=AstraCS:your-token-here
ASTRA_DB_COLLECTION=langgraph_collection
# ASTRA_DB_KEYSPACE=default_keyspace  # Optional - omit to use AstraDB default

# Optional: LangChain Tracing
LANGCHAIN_API_KEY=lsv2_pt_your-key-here
LANGCHAIN_PROJECT=GenAIAPPWithOPENAI

# Optional: Alternative LLM APIs
OPENAI_API_KEY=sk-your-openai-key  # Fallback if OpenRouter not set
GROQ_API_KEY=gsk_your-groq-key      # For Groq models
```

### 2. Get AstraDB Credentials

1. Go to [astra.datastax.com](https://astra.datastax.com)
2. Create a new Serverless (Vector) database
3. Copy the **API Endpoint** (from Connect tab)
4. Generate an **Application Token** (Database Administrator role)
5. Create a collection (or let the app create it automatically)

### 3. Get OpenRouter API Key

1. Visit [openrouter.ai](https://openrouter.ai)
2. Sign up and create an API key
3. Add credits to your account (pay-as-you-go)

## 🚀 Usage

### Running the API Server

```bash
# Method 1: Using Uvicorn directly
uvicorn langgraph_pdf_webcrawl_router_agent:app --host 0.0.0.0 --port 8000 --reload

# Method 2: Using Python
python langgraph_pdf_webcrawl_router_agent.py
```

The server will start at `http://localhost:8000`

**Access the API Documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Populating Sample Data

Before asking questions, populate AstraDB with sample documents:

```bash
python populate_astradb.py
```

**Menu Options:**
1. **Populate with sample documents** - Adds 6 sample company documents
2. **Test retrieval** - Verify vector search is working
3. **Clear collection** - Delete all documents (use with caution!)
4. **Exit**

### API Endpoints

#### 1. Upload PDF

**Endpoint:** `POST /upload`

```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@document.pdf" \
  -F "chunk_size=1000" \
  -F "chunk_overlap=200"
```

**Parameters:**
- `file` (required): PDF file to upload
- `chunk_size` (optional): Max characters per chunk (default: 1000)
- `chunk_overlap` (optional): Character overlap between chunks (default: 200)

**Response:**
```json
{
  "filename": "document.pdf",
  "file_sha256": "abc123...",
  "total_pages": 10,
  "total_chunks": 25,
  "chunk_size": 1000,
  "chunk_overlap": 200,
  "collection": "langgraph_collection",
  "ingested_at": "2024-01-15T10:30:00Z",
  "already_existed": false
}
```

#### 2. Ask Question

**Endpoint:** `POST /ask`

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the security policies?",
    "top_k": 4,
    "max_web_results": 5
  }'
```

**Request Body:**
```json
{
  "question": "What are the latest advancements in quantum computing?",
  "top_k": 4,
  "max_web_results": 5
}
```

**Response:**
```json
{
  "question": "What are the security policies?",
  "route_decision": "ASTRADB",
  "answer": "According to the company security policy...",
  "retrieved_documents": [
    {
      "rank": 1,
      "source": "AstraDB | security_policy.pdf p.1",
      "content": "All employees must follow...",
      "metadata": {"page": 1, "source": "security_policy.pdf"}
    }
  ],
  "crawled_pages": [],
  "duration_seconds": 2.45
}
```

#### 3. List Documents

**Endpoint:** `GET /documents`

```bash
curl "http://localhost:8000/documents"
```

**Response:**
```json
{
  "total": 3,
  "documents": [
    {
      "filename": "security_policy.pdf",
      "file_sha256": "abc123...",
      "total_pages": 5,
      "total_chunks": 12,
      "ingested_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### 4. Health Check

**Endpoint:** `GET /health`

```bash
curl "http://localhost:8000/health"
```

**Response:**
```json
{
  "status": "ok",
  "llm_model": "qwen/qwen3-235b-a22b",
  "embedding_model": "qwen/qwen3-embedding-8b",
  "astradb_collection": "langgraph_collection",
  "ingested_documents": 3
}
```

## 🏗️ Architecture

### LangGraph State Machine

```
┌──────────┐
│  START   │
└────┬─────┘
     │
     ▼
┌──────────────┐
│   ROUTER     │ ◄─── Analyzes question + available documents
│   NODE       │
└──────┬───────┘
       │
       ├─────────────┬──────────────┐
       │             │              │
       ▼             ▼              ▼
  ASTRADB      WEB_CRAWL       (fallback)
  RETRIEVAL    RETRIEVAL
       │             │
       └──────┬──────┘
              │
              ▼
       ┌──────────────┐
       │  RESPONSE    │
       │  GENERATOR   │
       └──────┬───────┘
              │
              ▼
          ┌───────┐
          │  END  │
          └───────┘
```

### Routing Logic

**ASTRADB Route:**
- Question contains domain-specific terms
- Proper nouns/names that could be in documents
- Single-word queries when documents exist
- Not time-sensitive

**WEB_CRAWL Route:**
- Time-sensitive queries ("latest", "recent", "current")
- General knowledge questions
- No documents uploaded
- Terms unlikely to be in uploaded docs

### Data Flow

1. **PDF Upload** → Text Extraction → Chunking → Embedding → AstraDB Storage
2. **Question** → Router → Retrieval (AstraDB OR Web) → LLM Generation → Response
3. **Web Crawl** → DuckDuckGo Search → Page Fetch → HTML Cleaning → Context Assembly

## 🔩 Configuration

### config.py - Shared Configuration

**Key Functions:**
- `create_embeddings()` - OpenRouter embeddings with raw string input
- `create_llm()` - Chat model initialization (Qwen by default)
- `create_vector_store()` - AstraDB connection with retry logic
- `validate_astra_config()` - DNS and credential validation

**Important Settings:**
```python
# Embedding Configuration
check_embedding_ctx_length=False  # Disable tokenization for OpenRouter
encoding_format="float"           # String input format
chunk_size=1                      # Process one text at a time

# LLM Configuration
model="qwen/qwen3-235b-a22b"      # 235B parameter model
temperature=0                      # Deterministic responses
```

### Web Crawl Constants

```python
WEB_SEARCH_MAX_RESULTS = 5        # Number of URLs to crawl
WEB_PAGE_MAX_CHARS = 4000         # Max chars per page
HTTP_TIMEOUT = 10                  # Request timeout (seconds)

BLOCKED_DOMAINS = {
    "youtube.com", "twitter.com", "instagram.com",
    "facebook.com", "tiktok.com", "linkedin.com", "reddit.com"
}
```

## 🐛 Troubleshooting

### Common Issues

#### 1. ModuleNotFoundError: No module named 'ddgs'

**Problem:** Import statement uses wrong module name

**Solution:** The package is `duckduckgo_search` not `ddgs`
```python
# Correct
from duckduckgo_search import DDGS

# Incorrect
from ddgs import DDGS
```

#### 2. OpenRouter 422 Error: "Input should be a valid string"

**Problem:** Tiktoken is sending token IDs instead of raw strings

**Solution:** Already fixed in config.py with:
```python
check_embedding_ctx_length=False  # Disables tokenization
```

#### 3. AstraDB 400 Error: Invalid keyspace

**Problem:** `default_keyspace` doesn't exist in your database

**Solution:** 
- **Option 1:** Omit `ASTRA_DB_KEYSPACE` from .env (uses AstraDB default)
- **Option 2:** Find actual keyspace name in AstraDB console and set it

#### 4. DNS Resolution Failed

**Problem:** Cannot connect to AstraDB endpoint

**Solutions:**
- Check `ASTRA_DB_API_ENDPOINT` in .env
- Verify database is active (not hibernated)
- Try `nslookup <your-astra-hostname>`
- Check VPN/firewall settings

#### 5. Quota Exceeded

**Problem:** OpenRouter API rate limit or credit exhaustion

**Solutions:**
- Add credits to OpenRouter account
- Check usage at openrouter.ai/activity
- Reduce `chunk_size` or `max_web_results`

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📁 Project Structure

```
agents_deploy/
│
├── .env                                    # Environment variables (not in git)
├── requirements.txt                        # Python dependencies
│
├── config.py                               # Shared configuration and factories
│   ├── create_embeddings()                # OpenRouter embeddings setup
│   ├── create_llm()                       # Chat model initialization
│   ├── create_vector_store()              # AstraDB connection
│   └── validate_astra_config()            # Config validation
│
├── langgraph_pdf_webcrawl_router_agent.py # Main FastAPI application
│   ├── FastAPI app initialization
│   ├── LangGraph state machine
│   ├── Router node (ASTRADB vs WEB_CRAWL)
│   ├── AstraDB retrieval node
│   ├── Web crawl retrieval node
│   ├── Response generator node
│   └── API endpoints (/upload, /ask, /documents, /health)
│
├── populate_astradb.py                    # Helper script for sample data
│   ├── Sample document templates
│   ├── Batch ingestion logic
│   ├── Test retrieval function
│   └── Collection management
│
└── README.md                               # This file
```

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 style guide
- Add docstrings to all functions
- Update README.md for new features
- Test with both AstraDB and Web Crawl routes
- Ensure error handling is comprehensive

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LangChain/LangGraph** - For the amazing orchestration framework
- **DataStax AstraDB** - For the serverless vector database
- **OpenRouter** - For unified LLM API access
- **FastAPI** - For the excellent web framework
- **DuckDuckGo** - For the privacy-focused search API

## 📞 Support

For issues, questions, or suggestions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Open an issue on GitHub
3. Review existing issues for solutions

---

**Built with ❤️ using LangGraph, FastAPI, and AstraDB**

**Version:** 3.0.0  
**Python:** 3.13.1  
**Last Updated:** 2024
