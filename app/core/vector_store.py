from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from app.core.config import settings
import uuid
import logging
import time

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index_name
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize Pinecone index with correct dimension"""
        try:
            existing_indexes = self.pc.list_indexes().names()
            
            if self.index_name in existing_indexes:
                index_info = self.pc.describe_index(self.index_name)
                current_dimension = index_info.dimension
                
                if current_dimension != settings.embedding_dimension:
                    self.pc.delete_index(self.index_name)
                    time.sleep(10)

                    self.pc.create_index(
                        name=self.index_name,
                        dimension=settings.embedding_dimension,
                        metric="cosine",
                        spec=ServerlessSpec(
                            cloud="aws",
                            region="us-east-1"
                        )
                    )

                    time.sleep(10)
                else:
                    logger.info("Index dimension matches requirements")
            else:
                self.pc.create_index(
                    name=self.index_name,
                    dimension=settings.embedding_dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                time.sleep(10)  
            
            self.index = self.pc.Index(self.index_name)
            
        except Exception as e:
            logger.error(f"Pinecone initialization failed: {e}")
            raise
    
    def upsert_vectors(
        self, 
        vectors: List[List[float]], 
        texts: List[str], 
        metadata: List[Dict[str, Any]]
    ) -> List[str]:
        """Insert vectors into Pinecone with metadata"""
        try:
            if not vectors or not texts:
                logger.warning("No vectors or texts to upsert")
                return []
                
            ids = [str(uuid.uuid4()) for _ in range(len(vectors))]

            for i, meta in enumerate(metadata):
                meta['text'] = texts[i]

            vectors_to_upsert = [
                (ids[i], vectors[i], metadata[i]) 
                for i in range(len(vectors))
            ]
            
           
            batch_size = 100
            successful_ids = []
            
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                try:
                    upsert_response = self.index.upsert(vectors=batch)
                    successful_ids.extend(ids[i:i + batch_size])
                
                except Exception as e:
                    logger.error(f"Failed to upsert batch {i//batch_size + 1}: {e}")
                    continue
            
            return successful_ids
        
        except Exception as e:
            logger.error(f"Vector upsert failed: {e}")
            raise
    
    def query(
        self, 
        query_vector: List[float], 
        top_k: int = 5,
        filter_dict: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Query similar vectors from Pinecone"""
        try:
            logger.info(f"Querying Pinecone with vector of dimension: {len(query_vector)}")
            logger.info(f"Looking for top {top_k} results")
            
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            
            for i, match in enumerate(results.matches):
                logger.info(f"Match {i+1}: Score={match.score:.4f}")
                if match.metadata.get('text'):
                    logger.info(f"         Text: {match.metadata['text'][:100]}...")
            
            return [
                {
                    'id': match.id,
                    'score': match.score,
                    'text': match.metadata.get('text', ''),
                    'metadata': match.metadata
                }
                for match in results.matches
            ]
        
        except Exception as e:
            logger.error(f"Vector query failed: {e}")
            return []