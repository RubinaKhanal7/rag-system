from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # pinecone
    pinecone_api_key: str
    pinecone_environment: str = "gcp-starter"
    pinecone_index_name: str = "rag-documents"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./rag_system.db"
    
    # Application
    app_name: str = "RAG System"
    app_version: str = "1.0.0"
    
    # Embedding 
    embedding_model: str = "all-MiniLM-L6-v2"  
    embedding_dimension: int = 384  
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()