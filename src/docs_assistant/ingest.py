"""Load documentation pages, split, ingest into VectorDB."""

import logging
import time
from typing import List
from dotenv import load_dotenv
load_dotenv()

from langchain_core.documents import Document
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore

from docs_assistant.load import load_docs
from docs_assistant.embeddings import get_embeddings_model
from docs_assistant.constants import INDEX_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def split_docs(docs: List[Document]) -> List[Document]:
    """
    Split documents by markdown headers and then further split by recursively look at characters.
    
    Args:
        docs: List of Document objects
    
    Returns:
        List of Document objects split by headers and then by character count
    """
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on, strip_headers=False)
    
    chunk_size = 2000
    chunk_overlap = 100
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    # Step 1: Split all documents by headers and preserve metadata
    header_split_docs = []
    for doc in docs:
        md_header_splits = markdown_splitter.split_text(doc.page_content)
        
        # Add original metadata to each split
        for split in md_header_splits:
            split.metadata.update(doc.metadata)
            header_split_docs.append(split)
    
    logger.info(f"No. of document chunks after markdown header split: {len(header_split_docs)}")

    # Step 2: Further split by character count
    final_splits = text_splitter.split_documents(header_split_docs)
    logger.info(f"No. of document chunks after recursive char split: {len(final_splits)}")

    return final_splits


def ingest_docs():

    # Load docs
    base_url = "https://microsoft.github.io/autogen/0.2/docs/"
    num_pages = 25
    docs_from_documentation = load_docs(base_url, num_pages)
    logger.info(f"No. of loaded documents: {len(docs_from_documentation)}")

    # Split docs
    docs_transformed = split_docs(docs_from_documentation)
    docs_transformed = [
        doc for doc in docs_transformed if len(doc.page_content) > 25
    ]
        
    # Ingest to Pinecone VectorDB
    logger.info(f"No. of documents to be added to VectorDB: {len(docs_transformed)}")
    vector_store = PineconeVectorStore.from_documents(
        documents=docs_transformed, 
        embedding=get_embeddings_model(), 
        index_name=INDEX_NAME
    )
    time.sleep(5)
    logger.info(f"Vector DB index stats:\n{vector_store._index.describe_index_stats()}")


if __name__ == "__main__":
    ingest_docs()

