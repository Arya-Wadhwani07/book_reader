from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    app_env: Literal["local", "cloud", "test"] = "local"
    session_secret: SecretStr = SecretStr("")
    state_backend: Literal["sqlite", "firestore"] = "sqlite"
    data_dir: Path = ROOT / ".data"
    gcp_project_id: str = "clean-mountain-511522-d0"
    gcp_region: str = "us-west1"
    gcs_bucket: str = ""
    ingestion_job: str = "book-companion-ingest"
    nvidia_api_key: SecretStr = SecretStr("")
    nvidia_model: str = ""
    anthropic_api_key: SecretStr = SecretStr("")
    anthropic_model: str = ""
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    tavily_api_key: SecretStr = SecretStr("")
    pinecone_api_key: SecretStr = SecretStr("")
    pinecone_index: str = "book-companion"
    openai_budget_usd: float = Field(default=5, gt=0, le=5)
    generation_budget_usd: float = Field(default=2.5, gt=0, le=2.5)
    max_upload_bytes: int = 25_000_000
    max_pdf_pages: int = 500
    max_words: int = 125_000
    max_tokens: int = 250_000
    session_days: int = 30

    @model_validator(mode="after")
    def validate_isolation(self):
        if len(self.session_secret.get_secret_value()) < 32:
            raise ValueError("SESSION_SECRET must contain at least 32 characters.")
        self.data_dir = self.data_dir.resolve()
        if not self.data_dir.is_relative_to(ROOT):
            raise ValueError("DATA_DIR must remain inside the project directory.")
        if self.app_env == "cloud" and (self.state_backend != "firestore" or not self.gcs_bucket):
            raise ValueError("Cloud deployment requires Firestore and GCS_BUCKET.")
        return self

    def available_providers(self):
        return [
            provider
            for provider in ("nvidia", "anthropic", "openai")
            if getattr(self, f"{provider}_api_key").get_secret_value()
            and getattr(self, f"{provider}_model")
        ]
