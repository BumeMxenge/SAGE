# Checks make sign-in's link against local Supabase: its token signs Mbali in, and the API then
# answers for her as a student who has finished setup. Her account stays afterwards, as it does
# after make sign-in.
import os
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient
from supabase import create_client

from sage.cli import main
from sage.config import get_settings
from sage.main import create_app

pytestmark = pytest.mark.integration


@pytest.fixture
def local_settings(url, monkeypatch):
    # What make sign-in hands the command, and make dev the app. Settings are cached, so they're
    # cleared before and after.
    monkeypatch.setenv("SUPABASE_URL", url)
    monkeypatch.setenv("SUPABASE_SECRET_KEY", os.environ["SAGE_TEST_SECRET_KEY"])
    # The app won't start without an OpenAI key. This test starts it but asks no question, so no
    # model is called and a stand-in does.
    monkeypatch.setenv("OPENAI_API_KEY", "not-a-real-key")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.usefixtures("approved_years")  # as make load runs before make sign-in
def test_the_link_signs_mbali_in_as_a_student(
    local_settings, url, capsys, fake_account
):
    # The second run finds the account the first made, as every later make sign-in does. Each run
    # prints the link and nothing else.
    main(["sign-in"])
    main(["sign-in"])
    _, link = capsys.readouterr().out.splitlines()
    token = parse_qs(urlsplit(link).query)["token_hash"][0]

    # The token swapped for a session, as the frontend does
    browser = create_client(url, os.environ["SAGE_TEST_PUBLISHABLE_KEY"])
    session = browser.auth.verify_otp(
        {"token_hash": token, "type": "magiclink"}
    ).session

    headers = {"Authorization": f"Bearer {session.access_token}"}
    with TestClient(create_app(), headers=headers) as api:
        assert api.get("/v1/me").json() == {
            "email": fake_account["email"],
            "account": "student",
            "student_number": "DLMMBA999",  # her address before the @, in capitals
            "onboarding_complete": True,  # her seeded profile says so
        }
