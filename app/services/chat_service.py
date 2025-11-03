from typing import List, Dict, Any, Optional
import json
import redis
from app.core.config import settings
from app.core.embeddings import EmbeddingService
from app.core.vector_store import VectorStore
import re
import logging

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
    
    def get_chat_history(self, session_id: str) -> List[Dict[str, str]]:
        """Retrieve chat history from Redis"""
        try:
            history_key = f"chat:{session_id}"
            history_json = self.redis_client.get(history_key)
            
            if history_json:
                return json.loads(history_json)
            return []
        except Exception as e:
            return []
    
    def save_chat_history(self, session_id: str, history: List[Dict[str, str]]):
        """Save chat history to Redis with 24-hour expiry"""
        try:
            history_key = f"chat:{session_id}"
            self.redis_client.setex(
                history_key, 
                86400,  
                json.dumps(history)
            )
        except Exception as e:
            logger.error(f"Error saving chat history: {e}")
    
    def add_message_to_history(self, session_id: str, role: str, content: str):
        """Add a message to chat history"""
        history = self.get_chat_history(session_id)
        history.append({"role": role, "content": content})

        if len(history) > 10:
            history = history[-10:]
        
        self.save_chat_history(session_id, history)
    
    def detect_booking_intent(self, query: str) -> bool:
        """Detect if user wants to book an interview"""
        booking_keywords = [
            'book', 'schedule', 'interview', 'appointment', 
            'meeting', 'slot', 'time', 'date', 'reserve'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in booking_keywords)
    
    def retrieve_context(self, query: str, top_k: int = 5) -> List[str]:
        """Retrieve relevant context from vector store"""
        try:
            query_embedding = self.embedding_service.generate_embedding(query)            
            results = self.vector_store.query(query_embedding, top_k=top_k)
            relevant_results = [result for result in results if result.get('score', 0) > 0.3]
            
            return [result['text'] for result in relevant_results if result.get('text')]
            
        except Exception as e:
            return []
    
    def generate_response(self, query: str, context: List[str], chat_history: List[Dict[str, str]]) -> str:
        """Generate response using rule-based system with RAG"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            return "Hello! I'm your AI assistant. I can help answer questions based on your uploaded documents or help you book an interview."
        
        if self.detect_booking_intent(query):
            return "I can help you book an interview! Please provide your name, email, preferred date (YYYY-MM-DD), and time (HH:MM)."
        
        if any(word in query_lower for word in ['thank', 'thanks']):
            return "You're welcome! Is there anything else I can help you with?"
        
        if context:
            combined_context = "\n\n".join(context)

            if "artificial intelligence" in query_lower or "ai" in query_lower:
                ai_sentences = [sentence for sentence in combined_context.split('.') 
                               if 'artificial intelligence' in sentence.lower() or 'ai' in sentence.lower()]
                if ai_sentences:
                    return f"Based on your documents: {ai_sentences[0].strip()}."
            
            if "machine learning" in query_lower or "ml" in query_lower:
                ml_sentences = [sentence for sentence in combined_context.split('.') 
                               if 'machine learning' in sentence.lower() or 'ml' in sentence.lower()]
                if ml_sentences:
                    return f"Based on your documents: {ml_sentences[0].strip()}."
            
            if len(combined_context) > 200:
                combined_context = combined_context[:197] + "..."
            
            return f"Based on the information in your documents:\n\n{combined_context}\n\nWould you like more specific details about any particular aspect?"
        

        return "I don't have enough relevant information in my knowledge base to answer that specific question. You might want to upload documents related to this topic, or try asking about artificial intelligence, machine learning, or other topics you've uploaded."
    
    def chat(self, session_id: str, query: str) -> Dict[str, Any]:
        """Main chat function with RAG"""
        try:
            chat_history = self.get_chat_history(session_id)
            context = self.retrieve_context(query)
            response = self.generate_response(query, context, chat_history)
            
            self.add_message_to_history(session_id, "user", query)
            self.add_message_to_history(session_id, "assistant", response)
            
            booking_detected = self.detect_booking_intent(query)
            
            return {
                "response": response,
                "context_used": context[:3],  
                "booking_detected": booking_detected,
                "booking_info": None
            }
        
        except Exception as e:
            logger.error(f"Chat error: {e}", exc_info=True)
            return {
                "response": "Sorry, I encountered an error while processing your request. Please try again.",
                "context_used": [],
                "booking_detected": False,
                "booking_info": None
            }