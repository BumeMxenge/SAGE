# Every environment variable, read once at startup (pydantic-settings)
from functools import lru_cache
from urllib.parse import urlsplit

from pydantic_settings import BaseSettings, SettingsConfigDict

# Supabase on this laptop: the only place sage sign-in and the integration tests may run, and where
# email-provider accounts, such as make sign-in's, may always sign in
LOCAL_HOSTS = {"127.0.0.1", "localhost"}


def is_local(url: str) -> bool:
    return urlsplit(url).hostname in LOCAL_HOSTS


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
    # Hosted SAGE takes only Microsoft sign-ins. ATP-5's test window switches this on, so the load
    # test's email-provider accounts can sign in too, then switches it off again.
    accept_email_sign_in: bool = False
    # The model that drafts rule trees the grammar can't read, and the key that pays for it, used
    # only by `sage ingest --draft`. Claude Haiku 5.5 is E2's choice, provisional until the advisor
    # milestone picks one model for drafting and the advisor.
    anthropic_api_key: str = ""
    drafting_model: str = "claude-haiku-5-5"

    @property
    def email_sign_in(self) -> bool:
        # Whether email-provider accounts count: always on local Supabase, and on a hosted project
        # only while accept_email_sign_in is on
        return self.accept_email_sign_in or is_local(self.supabase_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
