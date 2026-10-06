# Every environment variable, read once at startup (pydantic-settings)
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"
    git_sha: str = "dev"  # the commit the image was built from; "dev" on your laptop
    supabase_url: str = ""
    supabase_secret_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
