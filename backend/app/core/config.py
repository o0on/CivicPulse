from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "CivicPulse"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    DATABASE_URL: str = "postgresql+asyncpg://civicpulse:civicpulse_dev@postgres:5432/civicpulse"
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY: str = "dev-secret-key-civicpulse-development-only"
    CORS_ORIGINS: list[str] = ["http://frontend:3000"]
    TRIAGE_PROVIDER: str = "rules"
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    RATE_LIMIT_REQUESTS: int = 15
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    STATS_CACHE_TTL: int = 30
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
