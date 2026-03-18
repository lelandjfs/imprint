"""Imprint Chat API - FastAPI application."""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings
from routers import chat, filters, documents, theses

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# Set up LangSmith tracing if enabled
settings = get_settings()
logging.info(f"LangSmith config - tracing: {settings.langsmith_tracing}, api_key: {'SET' if settings.langsmith_api_key else 'NOT SET'}, project: {settings.langsmith_project}")

if settings.langsmith_tracing and settings.langsmith_api_key:
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    logging.info("✓ LangSmith tracing ENABLED")
else:
    logging.warning(f"✗ LangSmith tracing DISABLED - tracing={settings.langsmith_tracing}, has_key={bool(settings.langsmith_api_key)}")


# Create FastAPI app
app = FastAPI(
    title="Imprint Chat API",
    description="RAG chatbot for querying Imprint research knowledge base",
    version="1.0.0",
)


# CORS middleware
cors_origins_list = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(chat.router)
app.include_router(filters.router)
app.include_router(documents.router)
app.include_router(theses.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Imprint Chat API",
        "version": "1.0.0",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
