# Who a request comes from: what a verified sign-in token says, the kind of UCT account that makes
# it, and the interface that checks tokens
from typing import Literal, Protocol
from uuid import UUID

from sage.domain.base import Row


class Identity(Row):
    # What a verified sign-in token says about its account
    id: UUID
    email: str | None = None
    name: str | None = None  # from the account's metadata, never stored


class Account(Row):
    id: UUID
    email: str
    name: str | None = None
    kind: Literal["student", "staff"]
    student_number: str | None = None  # students only, from their email, never stored


class TokenVerifier(Protocol):
    # The identity a sign-in token proves. Raises NotSignedIn for a malformed, forged or expired one.
    def verify(self, token: str) -> Identity: ...
