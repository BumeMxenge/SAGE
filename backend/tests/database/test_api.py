# Checks the API end to end through the real adapters: a student-shaped local account, with Mbali
# seeded on it, gets her data back with a real sign-in token
import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from sage.config import get_settings
from sage.main import create_app
from sage.services.seed import load_seed, seed

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def student(new_account, stores, seed_file):
    account = new_account(student=True)
    seed(*stores, load_seed(seed_file, account.id))
    return account


@pytest.fixture(scope="module")
def api(url, student) -> Iterator[TestClient]:
    # The app as it starts on Azure, pointed at local Supabase. Settings are cached, so they're
    # cleared before and after.
    token = student.client.auth.get_session().access_token
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("SUPABASE_URL", url)
        patch.setenv("SUPABASE_SECRET_KEY", os.environ["SAGE_TEST_SECRET_KEY"])
        get_settings.cache_clear()
        headers = {"Authorization": f"Bearer {token}"}
        with TestClient(create_app(), headers=headers) as client:
            yield client
    get_settings.cache_clear()


def test_me(api, student):
    assert api.get("/v1/me").json() == {
        "email": student.email,
        "name": None,
        "account": "student",
        "student_number": student.email[:9].upper(),
        "onboarding_complete": True,
    }
