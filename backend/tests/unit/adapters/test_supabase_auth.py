# Checks the token verifier refuses forged tokens that make supabase-auth raise rather than reject
# them, and that a hosted project counts only Microsoft sign-ins unless ATP-5's setting is on. No
# network: a fake transport serves the project's published keys (JWKS).
import base64
import json
import time

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from supabase import create_client
from supabase.lib.client_options import SyncClientOptions

from sage.adapters.supabase.auth import SupabaseTokenVerifier
from sage.config import Settings
from sage.domain.errors import NotSignedIn, UctAccountRequired

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
HOSTED = "https://example.supabase.co"


def client_serving(key: dict, url: str = "http://127.0.0.1:54321"):
    keys = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"keys": [key]})
    )
    return create_client(
        url,
        "made-up-key",
        options=SyncClientOptions(httpx_client=httpx.Client(transport=keys)),
    )


@pytest.fixture
def verifier() -> SupabaseTokenVerifier:
    return SupabaseTokenVerifier(client_serving(KEY), accept_email=False)


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


@pytest.fixture(scope="module")
def signing_key() -> ec.EllipticCurvePrivateKey:
    # A real key pair, so a token passes the signature check and reaches the provider check
    return ec.generate_private_key(ec.SECP256R1())


def verifier_for(signing_key, **settings) -> SupabaseTokenVerifier:
    # Built as the app builds it, from the settings alone. No .env file, which holds real values.
    chosen = Settings(_env_file=None, **settings)
    public = jwt.algorithms.ECAlgorithm.to_jwk(signing_key.public_key(), as_dict=True)
    client = client_serving(public | {"kid": KID, "alg": "ES256"}, chosen.supabase_url)
    return SupabaseTokenVerifier(client, accept_email=chosen.email_sign_in)


def signed_in_with(signing_key, provider: str) -> str:
    claims = {
        "aud": "authenticated",
        "sub": "00000000-0000-4000-8000-000000000001",
        "email": "abcdef999@myuct.ac.za",
        "exp": int(time.time()) + 3600,
        "app_metadata": {"provider": provider},
    }
    return jwt.encode(claims, signing_key, algorithm="ES256", headers={"kid": KID})


def test_a_hosted_project_refuses_an_email_sign_in_while_the_setting_is_unset(
    signing_key,
):
    verifier = verifier_for(signing_key, supabase_url=HOSTED)
    with pytest.raises(UctAccountRequired):
        verifier.verify(signed_in_with(signing_key, "email"))


@pytest.mark.parametrize(
    "settings",
    [
        {"supabase_url": "http://127.0.0.1:54321"},
        {"supabase_url": HOSTED, "accept_email_sign_in": True},
    ],
    ids=["local Supabase", "hosted, in a test window"],
)
def test_an_email_sign_in_counts_locally_or_in_a_test_window(signing_key, settings):
    identity = verifier_for(signing_key, **settings).verify(
        signed_in_with(signing_key, "email")
    )
    assert identity.email == "abcdef999@myuct.ac.za"


def test_a_hosted_project_accepts_a_microsoft_sign_in(signing_key):
    verifier = verifier_for(signing_key, supabase_url=HOSTED)
    assert verifier.verify(signed_in_with(signing_key, "azure")).email == (
        "abcdef999@myuct.ac.za"
    )
