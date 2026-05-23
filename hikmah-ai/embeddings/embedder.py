"""
Embedding model wrapper — loads BAAI/bge-base-en-v1.5 directly via
sentence-transformers, bypassing LangChain's deprecated wrapper.

SSL verification is disabled so the model can be downloaded even on
networks with corporate proxies or missing root certificates.
After the first download the model is cached locally and no network
access is needed.
"""

from __future__ import annotations

import os
import ssl
from functools import lru_cache
from pathlib import Path
from typing import List

# ── Disable SSL verification BEFORE any network library is imported ──────────
os.environ.setdefault("CURL_CA_BUNDLE", "")
os.environ.setdefault("REQUESTS_CA_BUNDLE", "")
os.environ.setdefault("HF_HUB_DISABLE_SSL_VERIFICATION", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# Monkey-patch ssl so urllib3 / httpx also skip verification
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except Exception:
    pass

from sentence_transformers import SentenceTransformer  # noqa: E402

from utils.config import settings
from utils.logger import logger

# Model name — can be overridden via EMBEDDING_MODEL env var
_MODEL_NAME = settings.embedding_model  # default: BAAI/bge-base-en-v1.5

# Check if model was downloaded to local snapshot path (by download_model.py)
_LOCAL_SNAPSHOT = (
    Path.home() / ".cache/huggingface/hub/models--BAAI--bge-base-en-v1.5/snapshots/main"
)
if _LOCAL_SNAPSHOT.exists() and any(_LOCAL_SNAPSHOT.iterdir()):
    _MODEL_NAME = str(_LOCAL_SNAPSHOT)


# BGE models need this prefix on queries (not on documents) for best results
_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class HikmahEmbedder:
    """
    Singleton wrapper around SentenceTransformer.
    Loads the model once; subsequent calls reuse the cached instance.
    """

    _instance: "HikmahEmbedder | None" = None

    def __new__(cls) -> "HikmahEmbedder":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        logger.info(f"Loading embedding model: {_MODEL_NAME}")
        try:
            self._model = SentenceTransformer(
                _MODEL_NAME,
                device="cpu",
                trust_remote_code=False,
            )
            logger.info("Embedding model loaded successfully.")
        except Exception as exc:
            logger.error(f"Failed to load embedding model: {exc}")
            raise

        self._initialized = True

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query string (with BGE query prefix)."""
        return self._model.encode(
            _QUERY_PREFIX + text,
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of document strings (no prefix for documents)."""
        return self._model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            batch_size=32,
            show_progress_bar=False,
        ).tolist()

    @property
    def model(self) -> SentenceTransformer:
        return self._model


@lru_cache(maxsize=1)
def get_embedder() -> HikmahEmbedder:
    """Return the singleton embedder instance."""
    return HikmahEmbedder()
