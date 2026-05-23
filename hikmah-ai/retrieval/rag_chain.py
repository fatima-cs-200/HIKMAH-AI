"""
RAG chain — retrieval + LLM generation.

Uses Groq (cloud, free tier) as the LLM with llama3-8b-8192.
Falls back to Ollama if GROQ_API_KEY is not set.
No model download required for Groq.
"""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import AsyncIterator, List, Optional

# Load .env so GROQ_API_KEY is available even when imported directly
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser

from retrieval.retriever import HikmahRetriever, RetrievedChunk
from utils.config import settings
from utils.logger import logger

# Load system prompt
_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "system_prompt.txt"
_SYSTEM_TEMPLATE = _PROMPT_PATH.read_text(encoding="utf-8")


def _build_context(chunks: List[RetrievedChunk]) -> str:
    if not chunks:
        return "No relevant context was found in the Islamic sources."
    lines: List[str] = []
    for i, chunk in enumerate(chunks, 1):
        lines.append(f"[{i}] {chunk.citation}")
        if chunk.source == "quran":
            arabic = chunk.metadata.get("arabic", "")
            english = chunk.metadata.get("english", chunk.text)
            if arabic:
                lines.append(f"    Arabic: {arabic}")
            lines.append(f"    Translation: {english}")
        else:
            narrator = chunk.metadata.get("narrator", "")
            text = chunk.metadata.get("text", chunk.text)
            if narrator:
                lines.append(f"    Narrated by: {narrator}")
            lines.append(f"    Text: {text}")
        lines.append(f"    Confidence: {chunk.confidence_label} ({chunk.confidence_pct}%)")
        lines.append("")
    return "\n".join(lines)


def _build_llm():
    """Build LLM — Groq if API key available, else Ollama."""
    groq_key = os.environ.get("GROQ_API_KEY", "")

    if groq_key:
        logger.info("Using Groq LLM (llama3-8b-8192)")
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                api_key=groq_key,
                model="llama-3.3-70b-versatile",
                temperature=0.1,
                max_tokens=1024,
            )
        except Exception as e:
            logger.warning(f"Groq init failed: {e}. Falling back to Ollama.")

    logger.info(f"Using Ollama LLM ({settings.ollama_model})")
    from langchain_community.llms import Ollama
    return Ollama(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        temperature=0.1,
        num_predict=1024,
    )


class HikmahRAGChain:
    def __init__(self) -> None:
        self.retriever = HikmahRetriever()
        self._llm = _build_llm()
        self._output_parser = StrOutputParser()
        self._prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(_SYSTEM_TEMPLATE),
            HumanMessagePromptTemplate.from_template("{question}"),
        ])
        self._chain = self._prompt | self._llm | self._output_parser

    def query(self, question: str, top_k: int | None = None, source_filter: Optional[str] = None) -> dict:
        chunks = self.retriever.retrieve(question, top_k=top_k, source_filter=source_filter)
        context = _build_context(chunks)
        logger.info(f"Querying LLM with {len(chunks)} context chunks")
        try:
            answer = self._chain.invoke({"context": context, "question": question})
        except Exception as exc:
            logger.error(f"LLM call failed: {exc}")
            answer = (
                "I apologize, but I was unable to connect to the language model. "
                "Please ensure Ollama is running with the Llama 3 model loaded, "
                "or set a GROQ_API_KEY in your .env file for cloud-based responses."
            )
        sources = [
            {
                "citation": c.citation,
                "source": c.source,
                "confidence": c.confidence_pct,
                "confidence_label": c.confidence_label,
                "metadata": c.metadata,
            }
            for c in chunks
        ]
        return {"answer": answer, "sources": sources, "context_used": context, "chunks": chunks}

    async def astream_query(self, question: str, top_k: int | None = None, source_filter: Optional[str] = None) -> AsyncIterator[str]:
        chunks = self.retriever.retrieve(question, top_k=top_k, source_filter=source_filter)
        context = _build_context(chunks)
        try:
            async for token in self._chain.astream({"context": context, "question": question}):
                yield token
        except Exception as exc:
            logger.error(f"Streaming LLM call failed: {exc}")
            yield "I apologize, but I was unable to connect to the language model."
