# Who a request comes from: what a verified sign-in token says, the kind of UCT account that makes
# it, and the interface that checks tokens
from typing import Literal, Protocol
from uuid import UUID

from sage.shared.base import Row


class Identity(Row):
    # What a verified sign-in token says about its account. Never a name: SAGE neither stores nor
    # reads one, and the frontend asks Microsoft for it in the student's browser.
    id: UUID
    email: str | None = None


class Account(Row):
    id: UUID
    email: str
    kind: Literal["student", "staff"]
    # Students only, worked out from their email. SAGE's own tables never hold it.
    student_number: str | None = None


class TokenVerifier(Protocol):
    # The identity a sign-in token proves. Raises NotSignedIn for a malformed, forged or expired one.
    def verify(self, token: str) -> Identity: ...
