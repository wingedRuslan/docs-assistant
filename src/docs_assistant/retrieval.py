import logging
import time
from typing import Dict, Optional

from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_core.retrievers import BaseRetriever

from docs_assistant.config import get_retrieval_config
from docs_assistant.embeddings import get_embeddings_model


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_pc_retriever(config: Optional[Dict] = None) -> BaseRetriever:
    """
    Create and return a Pinecone-based retriever.
    
    Args:
        config: Configuration object containing search_kwargs
    
    Returns:
        A configured LangChain retriever
    """
    config = config or get_retrieval_config()
    
    pc = Pinecone()
    
    # Create index if it doesn't exist
    existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]
    if config.index_name not in existing_indexes:
        logger.info(f"Creating index {config.index_name}")
        pc.create_index(
            name=config.index_name,
            dimension=config.vector_dimension,
            metric=config.vector_metric,
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        while not pc.describe_index(config.index_name).status["ready"]:
            time.sleep(3)

    vector_store = PineconeVectorStore(
        index_name=config.index_name, 
        embedding=get_embeddings_model()
    )
    logger.info(f"Pinecone VectorStore <{config.index_name,}> stats:\n{vector_store._index.describe_index_stats()}")

    # Create and return the retriever
    return vector_store.as_retriever(
        search_type=config.search_type,
        search_kwargs=config.search_kwargs
    )

