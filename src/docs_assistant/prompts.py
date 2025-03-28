from langchain_core.prompts import PromptTemplate, ChatPromptTemplate


# hub.pull("langchain-ai/chat-langchain-rephrase")
REPHRASE_TEMPLATE = """
Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.

Chat History: 
{chat_history} 
Follow Up Input: {input} 
Standalone Question: 
"""

REPHRASE_PROMPT = PromptTemplate(
    input_variables=["chat_history", "input"],
    template=REPHRASE_TEMPLATE
)


# hub.pull("langchain-ai/retrieval-qa-chat")
QA_CHAT_RETRIEVAL_SYSTEM_TEMPLATE = """
You are a helpful assistant for question-answering tasks. 
Answer any user questions based on the context below:

<context>
{context}
</context>
"""

QA_CHAT_RETRIEVAL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", QA_CHAT_RETRIEVAL_SYSTEM_TEMPLATE),
    ("human", "Question: {input}"),
])

