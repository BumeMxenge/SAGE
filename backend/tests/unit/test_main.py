# Checks the app won't start without its Supabase settings, so a bad deploy fails at once rather
# than on every request
import pytest
from fastapi.testclient import TestClient

from sage.config import get_settings
from sage.main import create_app


@pytest.fixture
def no_supabase(monkeypatch):
    # Settings are cached, so clear them before and after
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_missing_supabase_settings_stop_startup(no_supabase):
    with pytest.raises(RuntimeError, match="SUPABASE_URL"), TestClient(create_app()):
        pass
