# The app with its stores swapped for in-memory fakes, and a made-up token for each kind of account.
# Mbali is seeded on her account and a copy of her data on another student's, so tests can check
# neither ever sees the other's rows.
from collections.abc import Callable
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sage.adapters.memory.auth import FakeTokenVerifier
from sage.adapters.memory.rules import InMemoryRuleRepository
from sage.adapters.memory.students import InMemoryStudentRepository
from sage.api import deps
from sage.domain.accounts import Identity
from sage.main import create_app
from sage.services.seed import load_seed, seed

MBALI = UUID("00000000-0000-4000-8000-000000000001")
ZVSORW = UUID(
    "00000000-0000-4000-8000-000000000002"
)  # another student, with her own plans
QRTILV = UUID(
    "00000000-0000-4000-8000-000000000003"
)  # a student who hasn't started setup


@pytest.fixture
def stores(seed_file) -> tuple[InMemoryRuleRepository, InMemoryStudentRepository]:
    rules, students = InMemoryRuleRepository(), InMemoryStudentRepository()
    for account in (MBALI, ZVSORW):
        seed(rules, students, load_seed(seed_file, account))
    return rules, students


@pytest.fixture
def app(stores, fake_account) -> FastAPI:
    identities = {
        "mbali": Identity(id=MBALI, **fake_account),
        "zvsorw": Identity(
            id=ZVSORW, email="zvsorw999@myuct.ac.za", name="Orwen Zvasko"
        ),
        "qrtilv": Identity(
            id=QRTILV, email="qrtilv999@myuct.ac.za", name="Ilvane Qorthu"
        ),
        "staff": Identity(
            id=UUID(int=4), email="test.advisor@uct.ac.za", name="Test Advisor"
        ),
        "outsider": Identity(id=UUID(int=5), email="outsider@example.com"),
    }
    app = create_app()
    app.dependency_overrides[deps.verifier] = lambda: FakeTokenVerifier(identities)
    app.dependency_overrides[deps.students] = lambda: stores[1]
    return app


@pytest.fixture
def signed_in(app) -> Callable[[str], TestClient]:
    # A client that sends the named account's token, as the frontend will
    def client(token: str) -> TestClient:
        return TestClient(app, headers={"Authorization": f"Bearer {token}"})

    return client
