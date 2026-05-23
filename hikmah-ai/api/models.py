"""
Pydantic request / response models for the HIKMAH AI API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000, description="The Islamic question to answer")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of context chunks to retrieve")
    source_filter: Optional[str] = Field(
        default=None,
        description="Filter results to 'quran', 'hadith', or None for both",
    )
    stream: bool = Field(default=False, description="Enable streaming response")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "What does Islam say about patience?",
                "top_k": 5,
                "source_filter": None,
                "stream": False,
            }
        }


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)
    source: str = Field(default="all", description="'quran', 'hadith', or 'all'")
    top_k: int = Field(default=10, ge=1, le=50)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class SourceReference(BaseModel):
    citation: str
    source: str
    confidence: int
    confidence_label: str
    metadata: Dict[str, Any]


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceReference]
    context_used: str
    question: str
    total_sources: int


class SearchResult(BaseModel):
    doc_id: str
    text: str
    source: str
    citation: str
    confidence: int
    confidence_label: str
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    query: str


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    ollama_connected: bool
    quran_verses: int
    hadith_count: int


class StatsResponse(BaseModel):
    quran_verses: int
    hadith_count: int
    embedding_model: str
    llm_model: str
    chroma_path: str
