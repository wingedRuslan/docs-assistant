import streamlit as st
from typing import Set, List, Dict, Any
from dotenv import load_dotenv
load_dotenv()

from docs_assistant.qa_chain import run_docs_qa_chat

# Page configuration
st.set_page_config(
    page_title="Docs Assistant",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Custom CSS for a clean, modern look
st.markdown(
    """
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stTextInput > div > div > input {
        background-color: #ffffff;
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        border: none;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .user {
        background-color: #e6f7ff;
        border-left: 5px solid #1890ff;
    }
    .assistant {
        background-color: #f6ffed;
        border-left: 5px solid #52c41a;
    }
    .source-text {
        font-size: 0.85rem;
        color: #666;
        margin-top: 0.5rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

def format_sources(sources: Set[str]) -> str:
    """Format source URLs into a clickable string."""
    if not sources:
        return ""
    return "\n".join(f"- [{url}]({url})" for url in sorted(sources))

def get_sources_from_results(result: Dict[str, Any]) -> Set[str]:
    """Extract source URLs from retrieval results."""
    sources = set()
    if "context" in result and result["context"]:
        for doc in result["context"]:
            if hasattr(doc, "metadata") and "source" in doc.metadata:
                sources.add(doc.metadata["source"])
    return sources

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "user_prompt_history" not in st.session_state:
    st.session_state["user_prompt_history"] = []
if "chat_answers_history" not in st.session_state:
    st.session_state["chat_answers_history"] = []
if "sources_history" not in st.session_state:
    st.session_state["sources_history"] = []

# App title
st.title("📚 Docs Assistant")
st.markdown("Ask questions about the documentation and get instant answers")

# Simple k-slider in sidebar
with st.sidebar:
    st.title("Settings")
    k_docs = st.slider(
        "Number of docs to retrieve", 
        min_value=1, 
        max_value=10, 
        value=5
    )
    
    if st.button("Clear Conversation"):
        st.session_state["chat_history"] = []
        st.session_state["user_prompt_history"] = []
        st.session_state["chat_answers_history"] = []
        st.session_state["sources_history"] = []

# Chat input - Simple local variable approach
user_query = st.text_input("Ask a question:", placeholder="What would you like to know?")

# Process input
if user_query:
    with st.spinner("Thinking..."):
        # Get response using the k parameter from the slider
        result = run_docs_qa_chat(
            query=user_query, 
            chat_history=st.session_state["chat_history"],
            # k=k_docs  # TODO
        )
        
        # Extract sources
        sources = get_sources_from_results(result)
        
        # Update session state histories
        st.session_state["user_prompt_history"].append(user_query)
        st.session_state["chat_answers_history"].append(result["answer"])
        st.session_state["sources_history"].append(sources)
        
        # Update chat history for context in future questions
        st.session_state["chat_history"].append(("user", user_query))
        st.session_state["chat_history"].append(("assistant", result["answer"]))

# Display chat history
if st.session_state["chat_answers_history"]:
    for i in range(len(st.session_state["chat_answers_history"])):
        # User message
        st.chat_message("user").write(st.session_state["user_prompt_history"][i])
        
        # Assistant message with sources
        message_container = st.chat_message("assistant")
        message_container.write(st.session_state["chat_answers_history"][i])
        
        # Show sources if available
        if i < len(st.session_state["sources_history"]) and st.session_state["sources_history"][i]:
            with message_container.expander("Sources"):
                st.markdown(format_sources(st.session_state["sources_history"][i]))

# Simple footer
st.caption("Docs Assistant - Chat with your documentation")
