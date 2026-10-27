from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cấu hình đọc từ biến môi trường / file .env (tương đương ConfigService của NestJS)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    database_url: str = "postgresql+asyncpg://docmind:docmind@db:5432/docmind"

    # LLM provider: đổi bằng env, không sửa code (xem Module 3)
    llm_provider: str = "gemini"
    llm_model: str = "gemini-2.5-flash"
    gemini_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
