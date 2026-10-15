from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "ai_tech_consultant"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_tech_consultant"

    # Knowledge Brain API & Security
    TASK1_PORT: int = 8001
    TASK1_API_KEY: str = "kb_dev_secret_key_12345"

    # Crawler Settings
    SITEMAP_URL: str = "https://support.brilliantdirectories.com/support/sitemap.xml"
    CRAWL_MAX_PAGES: int = 20
    CRAWL_CONCURRENCY: int = 2
    CRAWL_DELAY_SECONDS: float = 0.5
    CRAWL_TIMEOUT_SECONDS: float = 15.0
    USER_AGENT: str = "AITechConsultantBot/1.0 (+https://businesslabs.ai/bot)"

    # AI / Model Settings
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-7-sonnet-20250219"
    ANTHROPIC_EVAL_MODEL: str = "claude-3-5-haiku-20241022"
    USE_MOCK_LLM: bool = True

    # RAG Settings
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 80
    RETRIEVAL_TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.65
    EMBEDDING_DIM: int = 384




settings = Settings()
