from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "WinTAI"
    app_version: str = "0.1.0"
    debug: bool = True
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: list[str] = ["*"]

    tool_similarity_threshold: float = 0.55
    app_similarity_threshold: float = 0.55

    stt_language: str = "en"
    stt_model_arch: int | None = None
    stt_sample_rate: int = 16000
    stt_silence_timeout: float = 2.0
    stt_max_duration: float = 30.0

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
