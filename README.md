#Customer Support System

An customer support platform designed to simulate realistic customer interactions and assist support agents with intelligent response guidance.

The system combines a **Customer Simulator Agent**, **Support Knowledge Base with RAG**, **semantic search**, **conversation management**, and **FastAPI/Streamlit interfaces** to create a realistic customer-support training environment.

---

##  Project Overview

Customer support agents need to handle different types of customers, issues, emotions, and support scenarios.

This project provides an AI-powered environment where:

- Customers can be simulated using different personas.
- Customer emotions and patience can change dynamically.
- Support knowledge can be ingested from documents.
- Relevant information can be retrieved using semantic search.
- Conversations can be stored and managed.
- APIs are provided through FastAPI.
- A Streamlit interface can be used for demonstration and testing.

---

# Key Features

## Customer Simulator Agent

- Simulates realistic customer conversations.
- Supports different customer personas.
- Supports different support scenarios.
- Tracks customer emotional state.
- Tracks customer patience level.
- Considers issue severity.
- Considers expected resolution.
- Uses recent conversation history.
- Generates dynamic responses using an LLM.
- Provides a fallback response engine if external inference fails.

## Support Knowledge Base

- Upload PDF, TXT, and Markdown documents.
- Extract text from PDF documents using PyMuPDF.
- Clean extracted text.
- Split documents into overlapping chunks.
- Generate embeddings using Sentence Transformers.
- Store embeddings in ChromaDB.
- Perform semantic similarity search.
- Maintain document and page-level metadata.

## Backend

- FastAPI REST API.
- Swagger API documentation.
- Conversation management.
- Customer simulator API.
- Knowledge-base ingestion API.
- Semantic search API.

## Frontend / Demo

- Streamlit demonstration interface.
- Customer simulation interface.
- Knowledge-base demonstration.
- API interaction and testing.

## Testing

- Pytest test suite.
- Text-cleaning tests.
- Chunking tests.
- Metadata tests.
- TXT loading tests.
- API health tests.
- Simulator tests.

## Deployment

- Docker support.
- Docker Compose support.
- Environment-variable based configuration.

---

# System Architecture

```text
                         AI Customer Support System
                                   │
             ┌─────────────────────┴─────────────────────┐
             │                                           │
             ▼                                           ▼
     Customer Simulator                         Support Knowledge Base
             │                                           │
             ▼                                           ▼
    Customer Configuration                       Document Upload
             │                                           │
             ▼                                           ▼
    Conversation History                         Text Extraction
             │                                           │
             ▼                                           ▼
        LLM Prompt                                  Text Cleaning
             │                                           │
             ▼                                           ▼
    Customer Response                               Chunking
             │                                           │
             ▼                                           ▼
    Emotion + Patience                         Sentence Embeddings
             │                                           │
             │                                           ▼
             │                                      ChromaDB
             │                                           │
             │                                           ▼
             │                                    Semantic Search
             │
             └──────────────────┬────────────────────────┘
                                │
                                ▼
                           FastAPI Backend
                                │
                                ▼
                         Streamlit Interface


Support Agent Message
          │
          ▼
Conversation History
          │
          ▼
Customer Configuration
          │
          ├── Persona
          ├── Scenario
          ├── Current Emotion
          ├── Issue Severity
          ├── Patience Level
          └── Expected Resolution
          │
          ▼
       LLM Prompt
          │
          ▼
 Customer Simulator Agent
          │
          ├── Customer Message
          ├── Current Emotion
          └── Patience Level
          │
          ▼
    Conversation Storage


LLM Inference
      │
      ▼
    Failure
      │
      ▼
Fallback Engine
      │
      ▼
Scenario-Consistent
Customer Response


PDF / TXT / Markdown
        │
        ▼
Document Upload
        │
        ▼
Text Extraction
        │
        ▼
Text Cleaning
        │
        ▼
Chunking + Overlap
        │
        ▼
Sentence Embeddings
        │
        ▼
ChromaDB
        │
        ▼
User Query
        │
        ▼
Query Embedding
        │
        ▼
Semantic Similarity Search
        │
        ▼
Top-K Relevant Chunks
        │
        ▼
Source Metadata
