"""
Semantic retriever for Quran and Hadith collections.

Queries ChromaDB using cosine similarity and returns ranked results
with metadata and confidence scores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from embeddings.embedder import get_embedder
from utils.config import settings
from utils.logger import logger


@dataclass
class RetrievedChunk:
    """A single retrieved document chunk with metadata and score."""

    doc_id: str
    text: str
    source: str          # "quran" | "sahih_bukhari"
    citation: str
    metadata: dict
    score: float         # cosine similarity [0, 1] — higher is better

    @property
    def confidence_label(self) -> str:
        if self.score >= 0.80:
            return "Very High"
        elif self.score >= 0.65:
            return "High"
        elif self.score >= 0.50:
            return "Medium"
        else:
            return "Low"

    @property
    def confidence_pct(self) -> int:
        return min(100, int(self.score * 100))


class HikmahRetriever:
    """
    Retrieves relevant Quran verses and Hadith for a given query.

    Supports:
    - Quran-only search
    - Hadith-only search
    - Combined search (default)
    """

    def __init__(self) -> None:
        self.embedder = get_embedder()
        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_persist_path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._quran_col = self.client.get_or_create_collection(
            name=settings.chroma_quran_collection,
            metadata={"hnsw:space": "cosine"},
        )
        self._hadith_col = self.client.get_or_create_collection(
            name=settings.chroma_hadith_collection,
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        source_filter: Optional[str] = None,  # "quran" | "hadith" | None
        threshold: float | None = None,
    ) -> List[RetrievedChunk]:
        """
        Retrieve the most relevant chunks for *query*.

        Args:
            query: Natural-language question.
            top_k: Number of results per collection (defaults to settings.top_k_results).
            source_filter: Restrict to a single source, or None for both.
            threshold: Minimum similarity score to include (defaults to settings.similarity_threshold).

        Returns:
            List of RetrievedChunk sorted by score descending.
        """
        k = top_k or settings.top_k_results
        min_score = threshold if threshold is not None else settings.similarity_threshold

        query_embedding = self.embedder.embed_query(query)
        results: List[RetrievedChunk] = []

        if source_filter in (None, "quran"):
            results.extend(self._query_collection(self._quran_col, query_embedding, k))

        if source_filter in (None, "hadith"):
            results.extend(self._query_collection(self._hadith_col, query_embedding, k))

        # Filter by threshold and sort by score
        results = [r for r in results if r.score >= min_score]
        results.sort(key=lambda r: r.score, reverse=True)

        logger.debug(f"Retrieved {len(results)} chunks for query: '{query[:60]}…'")
        return results

    def retrieve_quran(self, query: str, top_k: int | None = None) -> List[RetrievedChunk]:
        return self.retrieve(query, top_k=top_k, source_filter="quran")

    def retrieve_hadith(self, query: str, top_k: int | None = None) -> List[RetrievedChunk]:
        return self.retrieve(query, top_k=top_k, source_filter="hadith")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _query_collection(
        self,
        collection: chromadb.Collection,
        query_embedding: List[float],
        top_k: int,
    ) -> List[RetrievedChunk]:
        if collection.count() == 0:
            logger.warning(f"Collection '{collection.name}' is empty. Run ingestion first.")
            return []

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        chunks: List[RetrievedChunk] = []
        for doc_id, doc, meta, dist in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            # ChromaDB cosine distance → similarity: score = 1 - distance
            score = max(0.0, 1.0 - dist)
            chunks.append(
                RetrievedChunk(
                    doc_id=doc_id,
                    text=doc,
                    source=meta.get("source", "unknown"),
                    citation=meta.get("citation", ""),
                    metadata=meta,
                    score=score,
                )
            )
        return chunks
