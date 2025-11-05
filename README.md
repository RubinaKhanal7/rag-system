RAG System API

A FastAPI-based Retrieval-Augmented Generation system with document ingestion and conversational chat capabilities.

## Features

- Upload PDF/TXT documents with two chunking strategies
- Semantic search using Pinecone vector database
- Conversational chat with memory (Redis)
- Interview booking support

## Quick Start

### 1. Install Dependencies

pip install -r requirements.txt

### 2. Setup Environment

Create `.env` file:
PINECONE_API_KEY=your_api_key_here
PINECONE_INDEX_NAME=rag-documents
REDIS_HOST=localhost
REDIS_PORT=6379

### 3. Start Redis

redis-server

### 4. Run Application

uvicorn app.main:app --reload

Access API at: `http://localhost:8000`  
Documentation: `http://localhost:8000/docs`

## API Endpoints

### Upload Document

POST /api/ingest/upload

**Parameters:**
- `file`: PDF or TXT file
- `chunking_strategy`: `fixed_size` or `sentence_based`

**Example:**
curl -X POST "http://localhost:8000/api/ingest/upload" \
  -F "file=@document.pdf" \
  -F "chunking_strategy=fixed_size"

### Chat Query
POST /api/chat/query
**Body:**
```json
{
  "session_id": "user123",
  "query": "What is AI?"
}
```

**Example:**
curl -X POST "http://localhost:8000/api/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "user123", "query": "What is AI?"}'

### Book Interview

POST /api/chat/book-interview

**Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "interview_date": "2025-11-15",
  "interview_time": "14:00"
}
```

### Get Chat History
GET /api/chat/history/{session_id}

## Tech Stack

- FastAPI
- Pinecone (vector database)
- Redis (chat memory)
- SQLite (metadata)
- Sentence Transformers (embeddings)

## Testing

1. Upload a document:
curl -X POST "http://localhost:8000/api/ingest/upload" \
  -F "file=@test.txt" \
  -F "chunking_strategy=fixed_size"

2. Ask a question:
curl -X POST "http://localhost:8000/api/chat/query" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "query": "Hello"}'

## Requirements

- Python 3.8+
- Redis server
- Pinecone account