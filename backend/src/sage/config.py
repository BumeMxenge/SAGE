# Every environment variable, read once at startup (pydantic-settings)
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    git_sha: str = "dev"  # the commit the image was built from; "dev" on your laptop
    supabase_url: str = ""
    supabase_secret_key: str = ""
    # Websites whose pages may call this API from a browser (CORS), comma-separated.
    # The backend deploy sets the hosted frontend's address. The default is your laptop's frontend,
    # on port 3000, or 3001 and 3002 for worktrees.
    cors_origins: str = (
        "http://localhost:3000,http://localhost:3001,http://localhost:3002"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
