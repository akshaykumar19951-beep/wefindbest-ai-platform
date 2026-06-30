from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    APP_NAME: str = "WeFindBest AI API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql+psycopg2://admin:admin@127.0.0.1:5433/wefindbest"
    SECRET_KEY: str = "CHANGE_ME_TO_SOMETHING_RANDOM"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    EMAIL_TOKEN_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    DEFAULT_USER_QUOTA: int = 1000
    LOG_LEVEL: str = "INFO"
    AI_GATEWAY_DEFAULT_PROVIDER: str = "mock"
    AI_GATEWAY_DEFAULT_MODEL: str = "mock"
    AI_GATEWAY_FALLBACK_MODELS: list[str] = Field(default_factory=lambda: ["mock"])
    AI_GATEWAY_LOAD_BALANCING: str = "round_robin"
    AI_GATEWAY_MAX_RETRIES: int = 2
    AI_GATEWAY_TIMEOUT_SECONDS: int = 30
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    MISTRAL_API_KEY: str | None = None
    COHERE_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OPENROUTER_API_KEY: str | None = None
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("AI_GATEWAY_FALLBACK_MODELS", mode="before")
    @classmethod
    def parse_fallback_models(cls, value):
        if isinstance(value, str):
            return [model.strip() for model in value.split(",") if model.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
