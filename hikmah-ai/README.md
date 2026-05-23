# ☪️ HIKMAH AI

> **Production-grade Islamic RAG (Retrieval-Augmented Generation) application**  
> Authentic answers from the Quran and Sahih Bukhari — no hallucinations.

---

## ✨ Features

| Feature | Details |
|---|---|
| 📖 Quran Retrieval | 6,236 verses with Arabic text, English translation, Surah/Ayah metadata |
| 📜 Hadith Retrieval | Sahih Bukhari with book, chapter, narrator, hadith number |
| 🔍 Semantic Search | BAAI/bge-base-en-v1.5 embeddings + ChromaDB cosine similarity |
| 🤖 RAG Pipeline | LangChain + Ollama Llama 3 with strict hallucination prevention |
| 🛡️ Anti-Hallucination | Model answers ONLY from retrieved context; cites every source |
| 🎨 Premium UI | Dark luxury Islamic-tech design with gold accents |
| ⚡ Streaming | Server-Sent Events for real-time token streaming |
| 📊 Dashboard | System health, DB stats, chat analytics |
| 📥 Export | Download full chat history as JSON |

---

## 🏗️ Architecture

```
User Question
     │
     ▼
Streamlit Frontend (port 8501)
     │  HTTP POST /api/v1/query
     ▼
FastAPI Backend (port 8000)
     │
     ├─► HikmahRetriever
     │       │
     │       ├─► BAAI/bge-base-en-v1.5 (embed query)
     │       ├─► ChromaDB quran_verses (cosine search)
     │       └─► ChromaDB sahih_bukhari (cosine search)
     │
     ├─► Build context from top-k chunks
     │
     └─► Ollama Llama 3 (grounded generation)
              │
              ▼
         Structured Response
         (answer + citations + confidence scores)
```

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.10+**
2. **Ollama** — [install](https://ollama.com/download)
3. **Llama 3 model**

```bash
# Install Ollama, then pull the model
ollama pull llama3
```

### Installation

```bash
# 1. Clone / navigate to project
cd hikmah-ai

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment config
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
```

### Ingest Islamic Data

```bash
# Ingest Quran + Sahih Bukhari into ChromaDB
python ingestion/run_ingestion.py

# Force re-ingest
python ingestion/run_ingestion.py --force

# Ingest only Quran
python ingestion/run_ingestion.py --source quran
```

> **Note:** On first run, the ingestion script will attempt to download the full
> datasets from HuggingFace. If offline, it uses the built-in sample data
> (15 Quran verses + 12 Hadith) for demo purposes.

### Start the Application

**Terminal 1 — Backend:**
```bash
python start_backend.py
# API docs: http://localhost:8000/docs
```

**Terminal 2 — Frontend:**
```bash
python start_frontend.py
# App: http://localhost:8501
```

---

## 📁 Project Structure

```
hikmah-ai/
├── api/                    # FastAPI backend
│   ├── main.py             # App factory, CORS, lifespan
│   ├── routes.py           # All API endpoints
│   └── models.py           # Pydantic request/response models
│
├── ingestion/              # Data ingestion pipeline
│   ├── quran_ingestor.py   # Quran → ChromaDB
│   ├── hadith_ingestor.py  # Sahih Bukhari → ChromaDB
│   └── run_ingestion.py    # CLI entry point
│
├── retrieval/              # RAG pipeline
│   ├── retriever.py        # Semantic search over ChromaDB
│   └── rag_chain.py        # LangChain RAG chain with Ollama
│
├── embeddings/             # Embedding model wrapper
│   └── embedder.py         # BAAI/bge-base-en-v1.5 singleton
│
├── frontend/               # Streamlit UI
│   └── app.py              # Full dark luxury interface
│
├── prompts/                # LLM prompt templates
│   └── system_prompt.txt   # Hallucination-prevention system prompt
│
├── utils/                  # Shared utilities
│   ├── config.py           # Pydantic settings
│   └── logger.py           # Loguru structured logging
│
├── data/                   # Cached datasets (auto-created)
├── chroma_db/              # ChromaDB persistence (auto-created)
├── .streamlit/config.toml  # Streamlit theme
├── .env.example            # Environment template
├── requirements.txt        # Python dependencies
├── start_backend.py        # Backend launcher
└── start_frontend.py       # Frontend launcher
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/health` | System health check |
| GET | `/api/v1/stats` | DB and model statistics |
| POST | `/api/v1/query` | RAG query (full response) |
| POST | `/api/v1/query/stream` | RAG query (SSE streaming) |
| POST | `/api/v1/search` | Semantic search (no LLM) |
| GET | `/api/v1/search/quran?q=...` | Quran-only search |
| GET | `/api/v1/search/hadith?q=...` | Hadith-only search |

Full interactive docs: **http://localhost:8000/docs**

---

## ⚙️ Configuration

Edit `.env` to customise:

```env
OLLAMA_MODEL=llama3          # or llama3:8b, llama3:70b
TOP_K_RESULTS=5              # chunks retrieved per query
SIMILARITY_THRESHOLD=0.3     # minimum cosine similarity
```

---

## 🛡️ Hallucination Prevention

The system prompt strictly instructs the model to:
1. Answer **only** from retrieved context
2. Return `"I could not find authentic evidence..."` when context is insufficient
3. **Never** fabricate Quranic verses or hadith
4. **Always** cite the exact source with Surah/Ayah or Hadith number

---

## 📜 Data Sources

- **Quran**: Sahih International English translation
- **Hadith**: Sahih al-Bukhari (compiled by Imam Muhammad ibn Ismail al-Bukhari, 810–870 CE)

---

*Built with ❤️ for the Muslim Ummah*
