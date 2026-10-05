# Shared pytest fixtures for every backend test
import pytest
from fastapi.testclient import TestClient

from sage.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
