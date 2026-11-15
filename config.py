"""
Shared configuration and factory helpers for the GenAI-LangChain project.

Required .env variables:
  OPENROUTER_API_KEY      – OpenRouter API key (preferred)
  OPENAI_API_KEY          – Fallback if OPENROUTER_API_KEY is not set
  ASTRA_DB_API_ENDPOINT   – AstraDB Data API endpoint (https://...)
  ASTRA_DB_APPLICATION_TOKEN – AstraDB application token
  ASTRA_DB_COLLECTION     – (optional, default: "default_collection")
  ASTRA_DB_KEYSPACE       – (optional, default: "default_keyspace")
"""

import os
import sys
import time
import socket
from urllib.parse import urlparse

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_astradb import AstraDBVectorStore

# Import AWS Secrets Manager integration
from aws_secrets import initialize_environment

# Initialize environment from AWS Secrets Manager or .env file
initialize_environment()

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_COLLECTION = "default_collection"
DEFAULT_KEYSPACE = "default_keyspace"
openrouter_key = os.getenv("OPENROUTER_API_KEY")
openrouter_model = os.getenv("OPENROUTER_MODEL", "qwen/qwen3-embedding-8b")
openrouter_model_dimensions = int(os.getenv("OPENROUTER_MODEL_DIMENSIONS", 4096))
temperature = float(os.getenv("OPENROUTER_TEMPERATURE", 0.0))




# ──────────────────────────────────────────────
# Embeddings
# ──────────────────────────────────────────────
def create_embeddings() -> OpenAIEmbeddings:
    """
    Create embeddings using OpenRouter's OpenAI-compatible API.
    Falls back to direct OpenAI if OPENROUTER_API_KEY is not set.
    """
    

    if openrouter_key:
        print("🔑 Using OpenRouter API key for embeddings")
        return OpenAIEmbeddings(
        api_key=openrouter_key,
        base_url=OPENROUTER_BASE_URL,
        model=openrouter_model,
        dimensions=openrouter_model_dimensions,
        # Disable tokenization - OpenRouter expects raw strings, not token IDs
        check_embedding_ctx_length=False,
        # Force string input format
        encoding_format="float",
        # Set chunk size to 1 to avoid batching issues
        chunk_size=1,
        default_headers={
            "HTTP-Referer": "https://your-app-url.com",  # Optional: for OpenRouter analytics
            "X-Title": "AstraDB Population Script",       # Optional: app name in OpenRouter dashboard
            },
        )  
        

        
    else:
        print("❌ Neither OPENROUTER_API_KEY nor OPENAI_API_KEY is set in your .env file.")
        sys.exit(1)


# ──────────────────────────────────────────────
# LLM (Chat model)
# ──────────────────────────────────────────────
def create_llm(
    model: str = "qwen/qwen3-235b-a22b",
    temperature: float = 0,
    app_title: str = "GenAI-LangChain",
) -> ChatOpenAI:
    """
    Create a ChatOpenAI instance routed through OpenRouter (Qwen by default).
    Falls back to direct OpenAI (gpt-4o) if OPENROUTER_API_KEY is not set.

    Args:
        model: OpenRouter model identifier (e.g. "qwen/qwen3-235b-a22b",
               "openai/gpt-4o", "anthropic/claude-sonnet-4-20250514").
        temperature: Sampling temperature.
        app_title: Value for the X-Title header on OpenRouter.
    """
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if openrouter_key:
        print(f"🔑 Using OpenRouter API key for LLM (model: {model})")
        return ChatOpenAI(
            api_key=openrouter_key,
            base_url=OPENROUTER_BASE_URL,
            model=model,
            temperature=temperature,
            default_headers={
                "HTTP-Referer": "https://your-app-url.com",
                "X-Title": app_title,
            },
        )
    elif openai_key:
        fallback_model = "gpt-4o"
        print(f"🔑 OPENROUTER_API_KEY not found, falling back to OPENAI_API_KEY (model: {fallback_model})")
        return ChatOpenAI(
            api_key=openai_key,
            model=fallback_model,
            temperature=temperature,
        )
    else:
        print("❌ Neither OPENROUTER_API_KEY nor OPENAI_API_KEY is set in your .env file.")
        sys.exit(1)


# ──────────────────────────────────────────────
# AstraDB validation & vector store
# ──────────────────────────────────────────────
def validate_astra_config() -> None:
    """Validate AstraDB environment variables and DNS before attempting connection."""
    endpoint = os.getenv("ASTRA_DB_API_ENDPOINT", "")
    token = os.getenv("ASTRA_DB_APPLICATION_TOKEN", "")

    if not endpoint:
        print("❌ ASTRA_DB_API_ENDPOINT is not set in your .env file.")
        sys.exit(1)
    if not endpoint.startswith("https://"):
        print(f"❌ ASTRA_DB_API_ENDPOINT must start with 'https://'. Got: {endpoint}")
        sys.exit(1)
    if not token:
        print("❌ ASTRA_DB_APPLICATION_TOKEN is not set in your .env file.")
        sys.exit(1)

    hostname = urlparse(endpoint).hostname
    print(f"🔍 Resolving AstraDB host: {hostname}")
    try:
        socket.getaddrinfo(hostname, 443)
        print(f"✅ DNS resolution successful for {hostname}")
    except socket.gaierror:
        print(f"\n❌ DNS resolution failed for: {hostname}")
        print("   Possible causes:")
        print("   1. ASTRA_DB_API_ENDPOINT is incorrect or has a typo")
        print("   2. Corporate firewall/proxy is blocking DNS")
        print("   3. VPN is interfering with DNS resolution")
        print("   4. The AstraDB database may have been deleted")
        print(f"\n   Current value: {endpoint}")
        print(f"\n   Try running:  nslookup {hostname}")
        sys.exit(1)


def create_vector_store(embeddings: OpenAIEmbeddings) -> AstraDBVectorStore:
    """
    Create an AstraDB vector store with config validation and retry
    for transient rate-limit errors.
    """
    validate_astra_config()

    max_retries = 3
    # Get keyspace from env, use None if not set (lets AstraDB use default)
    keyspace = os.getenv("ASTRA_DB_KEYSPACE")
    if keyspace:
        print(f"📁 Using keyspace: {keyspace}")
    else:
        print("📁 No keyspace specified, using AstraDB default")
    
    for attempt in range(1, max_retries + 1):
        try:
            # Only pass namespace if explicitly set
            vector_store_kwargs = {
                "embedding": embeddings,
                "collection_name": os.getenv("ASTRA_DB_COLLECTION", DEFAULT_COLLECTION),
                "api_endpoint": os.getenv("ASTRA_DB_API_ENDPOINT"),
                "token": os.getenv("ASTRA_DB_APPLICATION_TOKEN"),
            }
            if keyspace:
                vector_store_kwargs["namespace"] = keyspace
            
            return AstraDBVectorStore(**vector_store_kwargs)
        except Exception as exc:
            error_msg = str(exc)
            if "insufficient_quota" in error_msg:
                print("\n❌ API quota exceeded. Please check your plan and billing.\n")
                sys.exit(1)
            if "getaddrinfo failed" in error_msg:
                print("\n❌ Cannot connect to AstraDB — DNS resolution failed.")
                print("   Check your ASTRA_DB_API_ENDPOINT and network connectivity.")
                sys.exit(1)
            if "429" in error_msg and attempt < max_retries:
                wait = 2 ** attempt
                print(f"⏳ Rate-limited. Retrying in {wait}s (attempt {attempt}/{max_retries})...")
                time.sleep(wait)
            else:
                raise