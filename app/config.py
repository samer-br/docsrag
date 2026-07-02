"""Application configuration, loaded from environment / .env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    llm_provider: str = "anthropic"          # anthropic | openai
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    generation_model: str = "claude-sonnet-4-6"
    max_tokens: int = 1024

    # Embeddings (local sentence-transformers model)
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Chunking
    chunk_size: int = 800
    chunk_overlap: int = 120

    # Retrieval
    top_k: int = 5
    use_graph_retrieval: bool = True
    graph_expansion: int = 2                 # neighbours to pull in per seed chunk

    # Paths
    data_dir: str = "data/sample_docs"
    index_dir: str = "storage"


@lru_cache
def get_settings() -> Settings:
    return Settings()
