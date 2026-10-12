# Checks the token verifier against local Supabase's real tokens: a session's token is accepted, and
# the same token with one claim changed is refused
import base64
import json

import pytest

from sage.adapters.supabase.auth import SupabaseTokenVerifier
from sage.domain.accounts import Identity
from sage.domain.errors import NotSignedIn

pytestmark = pytest.mark.integration


def token(account) -> str:
    return account.client.auth.get_session().access_token


def test_a_real_session_token_is_accepted(secret, new_account):
    account = new_account()
    identity = SupabaseTokenVerifier(secret).verify(token(account))
    assert identity == Identity(id=account.id, email=account.email)


def test_a_token_with_a_changed_claim_is_refused(secret, new_account):
    header, payload, signature = token(new_account()).split(".")
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    claims["email"] = "someone.else@example.com"
    forged = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    with pytest.raises(NotSignedIn):
        SupabaseTokenVerifier(secret).verify(f"{header}.{forged}.{signature}")
