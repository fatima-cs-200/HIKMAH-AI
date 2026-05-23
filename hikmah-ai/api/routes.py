"""
FastAPI route definitions for HIKMAH AI.
"""

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from api.models import (
    QueryRequest,
    QueryResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    SourceReference,
    HealthResponse,
    StatsResponse,
)
from retrieval.rag_chain import HikmahRAGChain
from retrieval.retriever import HikmahRetriever
from utils.config import settings
from utils.logger import logger

router = APIRouter()

# Lazy-initialised singletons (avoid loading models at import time)
_rag_chain: HikmahRAGChain | None = None
_retriever: HikmahRetriever | None = None


def get_rag_chain() -> HikmahRAGChain:
    global _rag_chain
    if _rag_chain is None:
        _rag_chain = HikmahRAGChain()
    return _rag_chain


def get_retriever() -> HikmahRetriever:
    global _retriever
    if _retriever is None:
        _retriever = HikmahRetriever()
    return _retriever


# ---------------------------------------------------------------------------
# Health & Stats
# ---------------------------------------------------------------------------

@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check system health including Ollama connectivity and ChromaDB stats."""
    retriever = get_retriever()

    # Test Ollama connectivity
    ollama_ok = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{settings.ollama_base_url}/api/tags")
            ollama_ok = resp.status_code == 200
    except Exception:
        pass

    quran_count = retriever._quran_col.count()
    hadith_count = retriever._hadith_col.count()

    return HealthResponse(
        status="healthy" if ollama_ok else "degraded",
        app_name=settings.app_name,
        version=settings.app_version,
        ollama_connected=ollama_ok,
        quran_verses=quran_count,
        hadith_count=hadith_count,
    )


@router.get("/stats", response_model=StatsResponse, tags=["System"])
async def get_stats():
    """Return database and model statistics."""
    retriever = get_retriever()
    return StatsResponse(
        quran_verses=retriever._quran_col.count(),
        hadith_count=retriever._hadith_col.count(),
        embedding_model=settings.embedding_model,
        llm_model=settings.ollama_model,
        chroma_path=settings.chroma_persist_dir,
    )


# ---------------------------------------------------------------------------
# Query (RAG)
# ---------------------------------------------------------------------------

@router.post("/query", response_model=QueryResponse, tags=["RAG"])
async def query(request: QueryRequest):
    """
    Answer an Islamic question using RAG.
    Retrieves relevant Quran verses and Hadith, then generates a grounded answer.
    """
    if request.stream:
        raise HTTPException(
            status_code=400,
            detail="Use /query/stream for streaming responses.",
        )

    logger.info(f"Query received: '{request.question[:80]}'")
    chain = get_rag_chain()

    result = chain.query(
        question=request.question,
        top_k=request.top_k,
        source_filter=request.source_filter,
    )

    sources = [SourceReference(**s) for s in result["sources"]]

    return QueryResponse(
        answer=result["answer"],
        sources=sources,
        context_used=result["context_used"],
        question=request.question,
        total_sources=len(sources),
    )


@router.post("/query/stream", tags=["RAG"])
async def query_stream(request: QueryRequest):
    """
    Stream an Islamic answer token by token using Server-Sent Events.
    """
    logger.info(f"Streaming query: '{request.question[:80]}'")
    chain = get_rag_chain()

    async def event_generator() -> AsyncIterator[dict]:
        async for token in chain.astream_query(
            question=request.question,
            top_k=request.top_k,
            source_filter=request.source_filter,
        ):
            yield {"data": token}
        yield {"data": "[DONE]"}

    return EventSourceResponse(event_generator())


# ---------------------------------------------------------------------------
# Semantic Search
# ---------------------------------------------------------------------------

@router.post("/search", response_model=SearchResponse, tags=["Search"])
async def semantic_search(request: SearchRequest):
    """
    Perform semantic search across Quran and/or Hadith collections.
    Returns ranked results without LLM generation.
    """
    retriever = get_retriever()
    source_filter = None if request.source == "all" else request.source

    chunks = retriever.retrieve(
        query=request.query,
        top_k=request.top_k,
        source_filter=source_filter,
    )

    results = [
        SearchResult(
            doc_id=c.doc_id,
            text=c.text,
            source=c.source,
            citation=c.citation,
            confidence=c.confidence_pct,
            confidence_label=c.confidence_label,
            metadata=c.metadata,
        )
        for c in chunks
    ]

    return SearchResponse(results=results, total=len(results), query=request.query)


@router.get("/search/quran", tags=["Search"])
async def search_quran(
    q: str = Query(..., min_length=2, description="Search query"),
    top_k: int = Query(default=5, ge=1, le=20),
):
    """Quick Quran-only semantic search."""
    retriever = get_retriever()
    chunks = retriever.retrieve_quran(q, top_k=top_k)
    return {
        "results": [
            {
                "citation": c.citation,
                "arabic": c.metadata.get("arabic", ""),
                "english": c.metadata.get("english", ""),
                "confidence": c.confidence_pct,
                "surah_number": c.metadata.get("surah_number"),
                "ayah_number": c.metadata.get("ayah_number"),
            }
            for c in chunks
        ],
        "total": len(chunks),
    }


@router.get("/search/hadith", tags=["Search"])
async def search_hadith(
    q: str = Query(..., min_length=2, description="Search query"),
    top_k: int = Query(default=5, ge=1, le=20),
):
    """Quick Hadith-only semantic search."""
    retriever = get_retriever()
    chunks = retriever.retrieve_hadith(q, top_k=top_k)
    return {
        "results": [
            {
                "citation": c.citation,
                "narrator": c.metadata.get("narrator", ""),
                "text": c.metadata.get("text", ""),
                "book_name": c.metadata.get("book_name", ""),
                "hadith_number": c.metadata.get("hadith_number"),
                "confidence": c.confidence_pct,
            }
            for c in chunks
        ],
        "total": len(chunks),
    }
