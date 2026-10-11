# Checks the token verifier refuses forged tokens that make supabase-auth raise rather than reject
# them. No network: a fake transport serves the project's published keys (JWKS).
import base64
import json
import time

import httpx
import pytest
from supabase import create_client
from supabase.lib.client_options import SyncClientOptions

from sage.adapters.supabase.auth import SupabaseTokenVerifier
from sage.domain.errors import NotSignedIn

KID = "made-up-key-id"
# An elliptic-curve (ES256) key, as the hosted project signs with. Only its type is ever read here.
KEY = {
    "kty": "EC",
    "crv": "P-256",
    "alg": "ES256",
    "kid": KID,
    "x": "made-up",
    "y": "made-up",
}


@pytest.fixture
def verifier() -> SupabaseTokenVerifier:
    keys = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"keys": [KEY]})
    )
    client = create_client(
        "http://127.0.0.1:54321",
        "made-up-key",
        options=SyncClientOptions(httpx_client=httpx.Client(transport=keys)),
    )
    return SupabaseTokenVerifier(client)


def part(value: dict | bytes) -> str:
    # One base64url part of a JWT
    raw = value if isinstance(value, bytes) else json.dumps(value).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def test_an_rs256_token_naming_the_projects_key_is_refused(verifier):
    # The RSA check can't load an elliptic-curve key, and raises PyJWT's own error
    header = {"alg": "RS256", "typ": "JWT", "kid": KID}
    claims = {"aud": "authenticated", "exp": int(time.time()) + 3600}
    with pytest.raises(NotSignedIn):
        verifier.verify(f"{part(header)}.{part(claims)}.{part(b'made-up-signature')}")


def test_a_token_that_isnt_ascii_is_refused(verifier):
    with pytest.raises(NotSignedIn):
        verifier.verify("é.é.é")
