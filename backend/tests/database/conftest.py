# Fixtures for the tests that run against local Supabase. `make test-integration` passes the URL and
# keys from `supabase status`; any other URL is refused, so these tests can't touch real data.
import os
import random
import string
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

import pytest
from postgrest import APIError
from supabase import Client, create_client

from sage.config import is_local
from sage.ingestion.review import Snapshot
from sage.services.ingest import approved_snapshot, load
from sage.shared.seed import load_seed, seed
from sage.shared.students import StudentState
from sage.shared.supabase.rules import SupabaseRuleRepository
from sage.shared.supabase.students import SupabaseStudentRepository


@dataclass(frozen=True)
class Account:
    id: UUID
    email: str
    client: Client  # signed in as this account, as her browser would be


@pytest.fixture(scope="session")
def url() -> str:
    url = os.environ["SAGE_TEST_SUPABASE_URL"]
    if not is_local(url):
        pytest.exit(f"Integration tests only run against local Supabase, not {url}", 1)
    return url


@pytest.fixture(scope="session")
def secret(url) -> Client:
    # The backend's access: the secret key skips row level security
    return create_client(url, os.environ["SAGE_TEST_SECRET_KEY"])


@pytest.fixture(scope="session")
def anon(url) -> Client:
    # A browser that hasn't signed in
    return create_client(url, os.environ["SAGE_TEST_PUBLISHABLE_KEY"])


@pytest.fixture(scope="session")
def approved_years(secret) -> tuple[Snapshot, ...]:
    # Every approved year, loaded once as make load loads it, as her plans point into 2026's rules
    snapshots = tuple(approved_snapshot(year) for year in (2023, 2026))
    for snapshot in snapshots:
        load(snapshot, SupabaseRuleRepository(secret), replace=False)
    return snapshots


@pytest.fixture(scope="session")
def stores(
    secret, approved_years
) -> tuple[SupabaseRuleRepository, SupabaseStudentRepository]:
    return SupabaseRuleRepository(secret), SupabaseStudentRepository(secret)


@pytest.fixture(scope="session")
def new_account(url, secret) -> Iterator[Callable[..., Account]]:
    made = []

    def make(*, student: bool = False) -> Account:
        # A student's address is six random letters and 999, so it can't be a real student's
        letters = "".join(random.choices(string.ascii_lowercase, k=6))
        email = f"{letters}999@myuct.ac.za" if student else f"{uuid4().hex}@example.com"
        password = uuid4().hex
        user = secret.auth.admin.create_user(
            {"email": email, "password": password, "email_confirm": True}
        ).user
        made.append(user.id)
        browser = create_client(url, os.environ["SAGE_TEST_PUBLISHABLE_KEY"])
        browser.auth.sign_in_with_password({"email": email, "password": password})
        return Account(UUID(user.id), email, browser)

    yield make
    for user_id in made:
        secret.auth.admin.delete_user(user_id)  # her rows go with the account


@pytest.fixture(scope="session")
def her(new_account, stores, seed_file) -> Account:
    # Account A, with Mbali written onto it exactly as sage seed writes her
    account = new_account()
    seed(*stores, load_seed(seed_file, account.id))
    return account


@pytest.fixture(scope="session")
def stranger(new_account) -> Account:
    # Account B, with nothing of its own
    return new_account()


@pytest.fixture(scope="session")
def mbali(her, seed_file) -> StudentState:
    # Her rows as seeded, with the ids the database holds
    return load_seed(seed_file, her.id)


@pytest.fixture(scope="session")
def refused() -> Callable[..., None]:
    # Sends a request and checks Postgres refuses it with this error code, and, when named, this
    # constraint, so a test can't pass because some other rule happened to refuse the row
    def check(request: Any, code: str, constraint: str = "") -> None:
        with pytest.raises(APIError) as error:
            request.execute()
        assert error.value.code == code, error.value.message
        assert constraint in error.value.message

    return check
