# A token verifier for unit tests: each made-up token stands for one identity, so tests sign in by name
from sage.domain.accounts import Identity
from sage.domain.errors import NotSignedIn


class FakeTokenVerifier:
    def __init__(self, identities: dict[str, Identity]) -> None:
        self._identities = identities

    def verify(self, token: str) -> Identity:
        try:
            return self._identities[token]
        except KeyError:
            raise NotSignedIn() from None
