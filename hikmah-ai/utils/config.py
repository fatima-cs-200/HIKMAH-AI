"""
Central configuration management for HIKMAH AI.
Loads settings from environment variables / .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    # App
    app_name: str = Field(default="HIKMAH AI", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")

    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="llama3", env="OLLAMA_MODEL")

    # ChromaDB
    chroma_persist_dir: str = Field(default="./chroma_db", env="CHROMA_PERSIST_DIR")
    chroma_quran_collection: str = Field(default="quran_verses", env="CHROMA_QURAN_COLLECTION")
    chroma_hadith_collection: str = Field(default="sahih_bukhari", env="CHROMA_HADITH_COLLECTION")

    # Embedding
    embedding_model: str = Field(default="BAAI/bge-base-en-v1.5", env="EMBEDDING_MODEL")

    # API
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_reload: bool = Field(default=True, env="API_RELOAD")

    # Retrieval
    top_k_results: int = Field(default=5, env="TOP_K_RESULTS")
    similarity_threshold: float = Field(default=0.3, env="SIMILARITY_THRESHOLD")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def chroma_persist_path(self) -> Path:
        return Path(self.chroma_persist_dir)


settings = Settings()
