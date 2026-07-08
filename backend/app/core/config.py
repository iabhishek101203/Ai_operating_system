from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration.

    The default allowed root is the backend parent directory during early
    development. Production builds should make allowed roots explicit.
    """

    model_config = SettingsConfigDict(env_prefix="AIOS_", env_file=".env", extra="ignore")

    allowed_roots: list[Path] = Field(default_factory=lambda: [Path.cwd()])
    max_search_results: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()
