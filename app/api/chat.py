from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from app.db.database import get_db
from app.services.chat_service import ChatService
from app.db.models import InterviewBooking
from typing import Optional

router = APIRouter(prefix="/api/chat", tags=["Conversational RAG"])

class ChatRequest(BaseModel):
    session_id: str
    query: str

class BookingRequest(BaseModel):
    name: str
    email: EmailStr
    interview_date: str
    interview_time: str


@router.post("/query")
async def chat_query(request: ChatRequest):
    """
    Query the RAG system with conversation support
    """
    try:
        chat_service = ChatService()
        result = chat_service.chat(
            session_id=request.session_id,
            query=request.query
        )
        
        return {
            "status": "success",
            "session_id": request.session_id,
            "query": request.query,
            "response": result["response"],
            "context_used": result["context_used"],
            "booking_detected": result["booking_detected"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/book-interview")
async def book_interview(
    request: BookingRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Book an interview slot
    """
    try:
        booking = InterviewBooking(
            name=request.name,
            email=request.email,
            interview_date=request.interview_date,
            interview_time=request.interview_time
        )
    
        db.add(booking)
        await db.commit()
        await db.refresh(booking)
        
        return {
            "status": "success",
            "message": "Interview booked successfully",
            "booking": {
                "id": booking.id,
                "name": booking.name,
                "email": booking.email,
                "interview_date": booking.interview_date,
                "interview_time": booking.interview_time,
                "created_at": booking.created_at.isoformat()
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    Retrieve chat history for a session
    """
    try:
        chat_service = ChatService()
        history = chat_service.get_chat_history(session_id)
        
        return {
            "status": "success",
            "session_id": session_id,
            "history": history
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))