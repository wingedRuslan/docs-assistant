
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chat_models import init_chat_model
from langchain_pinecone import PineconeVectorStore

from docs_assistant.embeddings import get_embeddings_model
from docs_assistant.prompts import REPHRASE_PROMPT, QA_CHAT_RETRIEVAL_PROMPT
from docs_assistant.constants import INDEX_NAME

load_dotenv()


def run_docs_qa_chat(query: str, chat_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Run a document Q&A chat system with conversation history awareness.

    Args:
        query: User's question or input
        chat_history: Previous conversation messages

    Returns:
        Dict containing 'input', 'chat_history', 'context' and 'answer'
    """
    if chat_history is None:
        chat_history = []
    
    retriever = PineconeVectorStore(
        index_name=INDEX_NAME, 
        embedding=get_embeddings_model()
    ).as_retriever()
    
    llm = init_chat_model(
        model="gpt-4o-mini", 
        model_provider="openai", 
        temperature=0
    )

    # chain to take conversation history -> generate a search query and return relevant documents
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, prompt=REPHRASE_PROMPT
    )

    # chain to pass a list of Documents to a model
    stuff_documents_chain = create_stuff_documents_chain(
        llm, QA_CHAT_RETRIEVAL_PROMPT
    )

    # chain to pass user inquiry to the retriever to fetch relevant documents 
    # pass those documents (and original inputs + chat history) to an LLM to generate a response
    docs_qa_chat = create_retrieval_chain(
        retriever=history_aware_retriever, combine_docs_chain=stuff_documents_chain
    )

    result = docs_qa_chat.invoke(input={"input": query, "chat_history": chat_history})
    
    return result


if __name__ == "__main__":
    run_docs_qa_chat()

