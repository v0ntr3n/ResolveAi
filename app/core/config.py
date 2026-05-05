from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Core settings
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DATABASE_URL: str = "sqlite:///./data/orders.db"
    VECTOR_INDEX_DIR: str = "./data/vector_index"
    AUTO_SEED_DATA: bool = True
    REFUND_APPROVAL_THRESHOLD: float = 50.0
    
    # Embedding settings (supports llama.cpp server)
    EMBEDDING_API_BASE: str = ""  # e.g., "http://localhost:8080/v1" for llama.cpp
    EMBEDDING_MODEL: str = "text-embedding-ada-002"  # or local model name
    EMBEDDING_API_KEY: str = ""  # Optional for local servers
    
    # Week 3: LangSmith tracing
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "resolveai-production"
    LANGSMITH_ORG: str = ""
    
    # Week 3: RAGAS evaluation (uses OpenAI for metrics)
    OPENAI_API_KEY: str = ""
    
    # Week 3: Prometheus metrics
    PROMETHEUS_ENABLED: bool = True
    METRICS_PORT: int = 9090
    
    # CORS settings for frontend integration
    CORS_ORIGINS: str = "http://localhost:3000"
    CORS_ALLOW_CREDENTIALS: bool = True
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
