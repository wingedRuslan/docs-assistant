from typing import Dict, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class RetrievalConfig(BaseSettings):
    """Configuration for document retrieval and embeddings."""
    
    # Embedding model configuration
    embedding_model_name: str = "text-embedding-3-small"

    # Vector store configuration
    index_name: str = "autogen-doc-index"
    vector_dimension: int = 1536
    vector_metric: str = "cosine"
    
    # Retrieval parameters
    search_type: Literal["similarity", "mmr", "similarity_score_threshold"] = "similarity"
    search_kwargs: Dict = {
        "k": 5,                     # No. docs to return
        "score_threshold": None,    # Minimum relevance threshold
        "fetch_k": None,            # mmr: num docs
        "lambda_mult": None,        # mmr: diversity
        "filter": None              # Filter by document metadata
    }
    
    # Configure .env file loading
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_retrieval_config() -> RetrievalConfig:
    """Get cached retrieval settings."""
    return RetrievalConfig()

