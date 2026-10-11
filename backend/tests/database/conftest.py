# Fixtures for the tests that run against local Supabase. `make test-integration` passes the URL and
# keys from `supabase status`; any other URL is refused, so these tests can't touch real data.
import os
import random
import string
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID, uuid4

import pytest
from postgrest import APIError
from supabase import Client, create_client

from sage.adapters.supabase import connect
from sage.adapters.supabase.rules import SupabaseRuleRepository
from sage.adapters.supabase.students import SupabaseStudentRepository
from sage.cli import LOCAL_HOSTS
from sage.services.seed import Seed, load_seed, seed


@dataclass(frozen=True)
class Account:
    id: UUID
    email: str
    client: Client  # signed in as this account, as her browser would be


@pytest.fixture(scope="session")
def url() -> str:
    url = os.environ["SAGE_TEST_SUPABASE_URL"]
    if urlsplit(url).hostname not in LOCAL_HOSTS:
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
def stores(url) -> tuple[SupabaseRuleRepository, SupabaseStudentRepository]:
    client = connect(url, os.environ["SAGE_TEST_SECRET_KEY"])
    return SupabaseRuleRepository(client), SupabaseStudentRepository(client)


@pytest.fixture(scope="session")
def new_account(url, secret) -> Iterator[Callable[..., Account]]:
    made = []

    def make(*, student: bool = False, name: str | None = None) -> Account:
        # A student's address is six random letters and 999, so it can't be a real student's
        letters = "".join(random.choices(string.ascii_lowercase, k=6))
        email = f"{letters}999@myuct.ac.za" if student else f"{uuid4().hex}@example.com"
        password = uuid4().hex
        user = secret.auth.admin.create_user(
            {
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {"full_name": name} if name else {},
            }
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
def mbali(her, seed_file) -> Seed:
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
