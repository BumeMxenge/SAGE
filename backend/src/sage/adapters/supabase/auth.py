# Checks Supabase access tokens with supabase-auth's get_claims. It checks the signature against the
# project's published keys (JWKS), cached for ten minutes, or for an HS256 token, such as local
# Supabase may issue, asks the Auth server. It doesn't check who a token is for, so this does.
from pydantic import ValidationError
from supabase import Client
from supabase_auth.errors import AuthApiError, AuthInvalidJwtError

from sage.domain.accounts import Identity
from sage.domain.errors import NotSignedIn


class SupabaseTokenVerifier:
    def __init__(self, client: Client) -> None:
        # Only ever reads tokens. Signing in on this shared client would put a student's session in
        # place of the secret key on every request after it.
        self._auth = client.auth

    def verify(self, token: str) -> Identity:
        try:
            claims = self._auth.get_claims(jwt=token)["claims"]
        except (AuthInvalidJwtError, ValidationError) as error:
            # Malformed, forged or expired. ValidationError is a header or payload that isn't JSON.
            raise NotSignedIn() from error
        except AuthApiError as error:
            # The Auth server refused an HS256 token. Its own failures (5xx) stay errors, so an
            # outage never signs anyone out.
            if error.status >= 500:
                raise
            raise NotSignedIn() from error
        if claims.get("aud") != "authenticated" or not claims.get("sub"):
            raise NotSignedIn()
        metadata = claims.get("user_metadata") or {}
        return Identity(
            id=claims["sub"],
            email=claims.get("email"),
            name=metadata.get("full_name") or metadata.get("name"),
        )
