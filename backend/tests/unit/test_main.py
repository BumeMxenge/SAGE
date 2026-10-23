# Checks the app won't start without the settings it needs, so a bad deploy fails at once rather than
# on every request
import pytest
from fastapi.testclient import TestClient

from sage.config import get_settings
from sage.main import create_app


@pytest.fixture
def settings(monkeypatch):
    # Settings are cached, so clear them before and after
    def given(**values: str) -> None:
        for name, value in values.items():
            monkeypatch.setenv(name, value)
        get_settings.cache_clear()

    yield given
    get_settings.cache_clear()


def test_missing_supabase_settings_stop_startup(settings):
    settings(SUPABASE_URL="", SUPABASE_SECRET_KEY="")
    with pytest.raises(RuntimeError, match="SUPABASE_URL"), TestClient(create_app()):
        pass


def test_a_missing_openai_key_stops_startup(settings):
    # Supabase's settings are made up, as startup checks the key before it connects to anything
    settings(
        SUPABASE_URL="http://127.0.0.1:54321",
        SUPABASE_SECRET_KEY="made-up",
        OPENAI_API_KEY="",
    )
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"), TestClient(create_app()):
        pass
