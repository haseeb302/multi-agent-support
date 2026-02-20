"""
Application configuration from environment variables.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root (parent of app/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"


class Settings(BaseSettings):
    """Settings loaded from env (and .env file)."""

    # API
    app_env: str = "development"

    # Pinecone (https://docs.pinecone.io/guides/get-started/overview)
    # Required: API key and index name to connect. Optional: dimension, model, region (for create/index docs).
    pinecone_api_key: str = ""
    pinecone_index_name: str = ""
    pinecone_dimension: int = 1536  # optional; used when creating index
    pinecone_model_name: str = (
        "llama-text-embed-v2"  # optional; integrated embedding model when creating index
    )
    pinecone_region: str = "us-east-1"  # optional; cloud region
    pinecone_namespace: str = (
        "__default__"  # namespace for records; use __default__ for default
    )
    # Record field name for text to embed (must match index field_map, e.g. "text" or "chunk_text")
    pinecone_text_field: str = "text"

    # LLM (for chat/agents; set in env)
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    # Paths (default to docs/ in project)
    customers_csv_path: str = ""
    retention_rules_path: str = ""
    customer_updates_log_path: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.customers_csv_path:
            self.customers_csv_path = str(DOCS_DIR / "customers.csv")
        if not self.retention_rules_path:
            self.retention_rules_path = str(DOCS_DIR / "retention_rules.json")
        if not self.customer_updates_log_path:
            self.customer_updates_log_path = str(
                PROJECT_ROOT / "data" / "customer_updates.log"
            )

    def require_pinecone(self) -> None:
        """Raise ValueError if required Pinecone settings are missing."""
        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY is required")
        if not self.pinecone_index_name:
            raise ValueError("PINECONE_INDEX_NAME is required")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
