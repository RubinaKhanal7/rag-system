from typing import List
import PyPDF2
from io import BytesIO
from app.core.chunking import TextChunker, ChunkingStrategy
from app.core.embeddings import EmbeddingService
from app.core.vector_store import VectorStore
from app.db.models import Document
import logging

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.chunker = TextChunker()
    
    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_file = BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            logger.info(f"Extracted {len(text)} characters from PDF")
            return text.strip()
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise ValueError(f"Failed to extract text from PDF: {e}")
    
    def extract_text_from_txt(self, file_content: bytes) -> str:
        """Extract text from TXT file"""
        try:
            text = file_content.decode('utf-8').strip()
            logger.info(f"Extracted {len(text)} characters from TXT")
            return text
        except Exception as e:
            logger.error(f"TXT extraction failed: {e}")
            raise ValueError(f"Failed to extract text from TXT: {e}")
    
    async def process_document(
        self, 
        filename: str, 
        file_content: bytes, 
        chunking_strategy: ChunkingStrategy
    ) -> Document:
        """
        Process document: extract text, chunk, embed, and store
        """
        try:
            file_type = filename.split('.')[-1].lower()
            
            logger.info(f"Processing {file_type} file: {filename}")
            
            if file_type == 'pdf':
                text = self.extract_text_from_pdf(file_content)
            elif file_type == 'txt':
                text = self.extract_text_from_txt(file_content)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            if not text:
                raise ValueError("No text extracted from document")


            chunks = self.chunker.chunk_text(text, chunking_strategy)
            
            if not chunks:
                raise ValueError("No chunks created from text")
            
            embeddings = self.embedding_service.generate_embeddings(chunks)
 
            metadata = [
                {
                    'filename': filename,
                    'file_type': file_type,
                    'chunking_strategy': chunking_strategy.value,
                    'chunk_index': i
                }
                for i in range(len(chunks))
            ]
            
            self.vector_store.upsert_vectors(embeddings, chunks, metadata)
            
            document = Document(
                filename=filename,
                file_type=file_type,
                chunking_strategy=chunking_strategy.value,
                chunk_count=len(chunks)
            )
            
            return document
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            raise