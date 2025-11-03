from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api import ingestion, chat
from app.db.database import init_db
from app.core.config import settings

app = FastAPI(title=settings.app_name)

# Include routers
app.include_router(ingestion.router)
app.include_router(chat.router)


@app.get("/")
async def root():
    return {
        "message": "RAG System API",
        "version": settings.app_version,
        "endpoints": {
            "document_ingestion": "/api/ingest/upload",
            "chat_query": "/api/chat/query",
            "book_interview": "/api/chat/book-interview",
            "chat_history": "/api/chat/history/{session_id}"
        }
    }
