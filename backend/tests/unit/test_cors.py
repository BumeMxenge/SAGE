# Checks browsers may call the API only from the frontend's address (CORS preflight)
import pytest
from fastapi.testclient import TestClient

from sage.config import get_settings
from sage.main import create_app


def preflight(client: TestClient, origin: str):
    # What a browser sends before a cross-site request: "may this page call you?"
    return client.options(
        "/health",
        headers={"Origin": origin, "Access-Control-Request-Method": "GET"},
    )


def test_local_frontend_allowed(client):
    response = preflight(client, "http://localhost:3000")
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_other_site_refused(client):
    response = preflight(client, "https://example.com")
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


@pytest.fixture
def hosted_client(monkeypatch):
    # As on Azure: the deploy sets CORS_ORIGINS. Settings are cached, so clear them before and after.
    monkeypatch.setenv("CORS_ORIGINS", "https://web.example, https://other.example")
    get_settings.cache_clear()
    yield TestClient(create_app())
    get_settings.cache_clear()


def test_origins_from_environment(hosted_client):
    for origin in ("https://web.example", "https://other.example"):
        assert preflight(hosted_client, origin).status_code == 200
    assert preflight(hosted_client, "http://localhost:3000").status_code == 400
