from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Financial Regulation Compliance Monitoring Agent"
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    fsc_legislation_notice_url: str = "https://www.fsc.go.kr/po040301"
    request_timeout_seconds: int = 10
    max_documents_to_analyze: int = 80
    max_fsc_pages_to_scan: int = 8
    seen_documents_db_path: str = "storage/seen_documents.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
