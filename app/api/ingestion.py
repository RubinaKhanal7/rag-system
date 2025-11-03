from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.services.document_service import DocumentService
from app.core.chunking import ChunkingStrategy
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ingest", tags=["Document Ingestion"])

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="PDF or TXT file"),
    chunking_strategy: str = Form(..., description="Chunking strategy: fixed_size or sentence_based"),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and process a document
    """
    if not file or not file.filename:
        logger.error("No file provided in request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    allowed_extensions = ('.pdf', '.txt')
    if not file.filename.lower().endswith(allowed_extensions):
        logger.error(f"Invalid file type: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {', '.join(allowed_extensions)} files are supported"
        )

    if chunking_strategy not in ['fixed_size', 'sentence_based']:
        logger.error(f"Invalid chunking strategy: {chunking_strategy}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chunking_strategy must be either 'fixed_size' or 'sentence_based'"
        )
    
    try:
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )

        strategy_enum = ChunkingStrategy(chunking_strategy)

        document_service = DocumentService()
        document = await document_service.process_document(
            filename=file.filename,
            file_content=file_content,
            chunking_strategy=strategy_enum
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)

        
        return {
            "status": "success",
            "message": "Document processed and stored successfully",
            "document_id": document.id,
            "filename": document.filename,
            "chunking_strategy": document.chunking_strategy,
            "chunk_count": document.chunk_count,
            "file_type": document.file_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )