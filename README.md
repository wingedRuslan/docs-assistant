# Docs Assistant: Chat With Your Documentation

**Turn Any Documentation into an Interactive AI Assistant**

Docs Assistant lets you transform static documentation into an intelligent, conversational interface. Every documentation deserves a chat interface. Give your users the power to chat with your documentation and get answers instantly. 

Inspired by [Chat LangChain](https://chat.langchain.com/), this project builds on [chat-langchain](https://github.com/langchain-ai/chat-langchain) project.

## Loading data
Load documentation from any website using a combination of headless browser crawling and Docling processing:
- Crawls the website using AsyncChromiumLoader to handle JavaScript-rendered content
- Processes HTML into clean Markdown using [Docling](https://github.com/docling-project/docling), [Langchain loaders](https://python.langchain.com/docs/integrations/document_loaders/#webpages)
- Returns content as LangChain Document objects

```
from docs_assistant.load import load_docs
docs = load_docs("https://microsoft.github.io/autogen/0.2/docs/")
```


## Installation

```bash
poetry install
playwright install
```

