from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "WinTAI"
    app_version: str = "0.1.0"
    debug: bool = True
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173"]

    tool_similarity_threshold: float = 0.55
    app_similarity_threshold: float = 0.55

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
