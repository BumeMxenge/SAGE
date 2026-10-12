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


@pytest.mark.stub("engine")
def test_a_wrong_seed_path_stops_startup(monkeypatch, tmp_path):
    # As on Azure, if the image left out mbali.json: the app never starts, so the deploy's health
    # check fails rather than a student's first onboarding
    monkeypatch.setenv("SUPABASE_URL", "http://127.0.0.1:54321")
    monkeypatch.setenv("SUPABASE_SECRET_KEY", "made-up-key")
    monkeypatch.setattr("sage.main.SEED_FILE", tmp_path / "mbali.json")
    get_settings.cache_clear()
    try:
        with pytest.raises(FileNotFoundError), TestClient(create_app()):
            pass
    finally:
        get_settings.cache_clear()
