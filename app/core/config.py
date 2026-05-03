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
    
    # Week 3: LangSmith tracing
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "resolveai-production"
    LANGSMITH_ORG: str = ""
    
    # Week 3: RAGAS evaluation (uses OpenAI for metrics)
    OPENAI_API_KEY: str = ""
    
    # Week 3: Prometheus metrics
    PROMETHEUS_ENABLED: bool = True
    METRICS_PORT: int = 9090


@lru_cache
def get_settings() -> Settings:
    return Settings()
