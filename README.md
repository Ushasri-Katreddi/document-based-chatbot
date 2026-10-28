
# Document-Based Chatbot

A document-grounded conversational AI application built with FastAPI,
LangChain, PostgreSQL, and ChromaDB.

## Overview

The application allows authenticated users to upload PDF, TXT, and
Markdown documents and ask questions answered using Retrieval-Augmented
Generation (RAG).

## Planned Features

- Document upload, validation, and ingestion
- Local embeddings and persistent ChromaDB storage
- Context-aware answers with source citations
- Conversation history stored in PostgreSQL
- Structured responses validated with Pydantic
- LangChain tool calling for document search, listing, and calculations
- Asynchronous FastAPI endpoints
- Automated tests and evaluation

## Technology Stack

- Python 3.12
- FastAPI and Uvicorn
- LangChain
- PostgreSQL and SQLAlchemy 2.x
- ChromaDB
- Pydantic v2
- pytest and HTTPX

## Project Status

Under development.

## License

MIT
