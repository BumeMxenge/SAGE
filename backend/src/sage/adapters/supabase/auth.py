# Checks Supabase access tokens with supabase-auth's get_claims. It checks the signature against the
# project's published keys (JWKS), cached for ten minutes, or for an HS256 token, such as local
# Supabase may issue, asks the Auth server. It doesn't check who a token is for, so this does.
# sign_in_token makes the one-time sign-in that `sage sign-in` prints.
from uuid import UUID

from jwt import PyJWTError
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
        # A JWT is three dot-separated parts of ASCII. Anything else is refused here, because
        # get_claims raises a bare ValueError for a token that isn't ASCII, and catching every
        # ValueError would hide Supabase's own faults too.
        if not token.isascii() or len(token.split(".")) != 3:
            raise NotSignedIn()
        try:
            claims = self._auth.get_claims(jwt=token)["claims"]
        except (AuthInvalidJwtError, PyJWTError, ValidationError) as error:
            # Malformed, forged or expired. ValidationError is a header or payload that isn't JSON,
            # and PyJWTError a header naming an algorithm the project's key isn't for.
            raise NotSignedIn() from error
        except AuthApiError as error:
            # The Auth server refused an HS256 token. Its own failures (5xx) stay errors, so an
            # outage never signs anyone out.
            if error.status >= 500:
                raise
            raise NotSignedIn() from error
        if claims.get("aud") != "authenticated" or not claims.get("sub"):
            raise NotSignedIn()
        return Identity(id=claims["sub"], email=claims.get("email"))


def sign_in_token(client: Client, email: str) -> tuple[UUID, str]:
    # The account's id, and a token that signs it in once, within the hour. The account is made
    # first, confirmed and with no password, because a link for an address with no account would
    # make one with a random password.
    try:
        client.auth.admin.create_user({"email": email, "email_confirm": True})
    except AuthApiError as error:
        if error.code != "email_exists":  # an earlier run made it
            raise
    link = client.auth.admin.generate_link({"type": "magiclink", "email": email})
    return UUID(link.user.id), link.properties.hashed_token
