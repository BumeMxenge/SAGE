# The app with its stores swapped for in-memory fakes, and a made-up token for each kind of account.
# The rules are the approved 2026, and Mbali's data is seeded twice on them, on her account and on
# another student's, so tests can check neither ever sees the other's rows.
from collections.abc import Callable
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sage.advisor.stubs import FixedAdvisor
from sage.engine.stubs import InterimEligibility, SeededPlanGenerator
from sage.main import create_app
from sage.shared.api import deps
from sage.shared.auth import Identity
from sage.shared.memory.auth import FakeTokenVerifier
from sage.shared.memory.rules import InMemoryRuleRepository
from sage.shared.memory.students import InMemoryStudentRepository
from sage.shared.rulebook import Rulebook
from sage.shared.seed import load_seed, seed
from tests.unit.accounts import MBALI, QRTILV, ZVSORW


@pytest.fixture
def stores(
    seed_file, result_symbols, approved_2026
) -> tuple[InMemoryRuleRepository, InMemoryStudentRepository]:
    rules, students = (
        InMemoryRuleRepository(result_symbols),
        InMemoryStudentRepository(),
    )
    rules.replace_year(approved_2026)
    for account in (MBALI, ZVSORW):
        seed(rules, students, load_seed(seed_file, account))
    return rules, students


@pytest.fixture
def app(stores, fake_account, seed_file) -> FastAPI:
    identities = {
        "mbali": Identity(id=MBALI, email=fake_account["email"]),
        "zvsorw": Identity(id=ZVSORW, email="zvsorw999@myuct.ac.za"),
        "qrtilv": Identity(id=QRTILV, email="qrtilv999@myuct.ac.za"),
        "staff": Identity(id=UUID(int=4), email="test.advisor@uct.ac.za"),
        "outsider": Identity(id=UUID(int=5), email="outsider@example.com"),
    }
    app = create_app()
    app.dependency_overrides[deps.verifier] = lambda: FakeTokenVerifier(identities)
    app.dependency_overrides[deps.students] = lambda: stores[1]
    rulebook = Rulebook(stores[0])
    app.dependency_overrides[deps.rulebook] = lambda: rulebook
    generator = SeededPlanGenerator(seed_file)
    app.dependency_overrides[deps.plan_generator] = lambda: generator
    app.dependency_overrides[deps.eligibility_checker] = InterimEligibility
    app.dependency_overrides[deps.advisor] = FixedAdvisor
    return app


@pytest.fixture
def signed_in(app) -> Callable[[str], TestClient]:
    # A client that sends the named account's token, as the frontend will
    def client(token: str) -> TestClient:
        return TestClient(app, headers={"Authorization": f"Bearer {token}"})

    return client


@pytest.fixture
def mbali(signed_in) -> TestClient:
    # Signed in as Mbali, with her data as seeded
    return signed_in("mbali")


@pytest.fixture
def unanswered(stores) -> None:
    # Puts her seeded set back as it was before she answered: nothing hidden and no answers
    students = stores[1]
    state = students.get(MBALI)
    students.replace(
        state.model_copy(
            update={
                "plan_sets": tuple(
                    row.model_copy(update={"answers": None}) for row in state.plan_sets
                ),
                "plans": tuple(
                    plan.model_copy(update={"hidden": False}) for plan in state.plans
                ),
            }
        )
    )


@pytest.fixture
def plan_ids(mbali) -> dict[int, str]:
    # Her plan ids by position, as the planner learns them from the set
    return {
        plan["position"]: plan["id"] for plan in mbali.get("/v1/plans").json()["plans"]
    }
