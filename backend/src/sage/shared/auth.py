# Who a request comes from: what a verified sign-in token says, the interface that checks tokens,
# and which kind of UCT account it is, from its email. A student's address is their student number
# at myuct.ac.za, and staff use uct.ac.za. Nobody else can use SAGE.
import re
from typing import Literal, Protocol
from uuid import UUID

from sage.shared.base import Row
from sage.shared.errors import UctAccountRequired

STUDENT_EMAIL = re.compile(r"([a-z]{6}[0-9]{3})@myuct\.ac\.za")
STAFF_DOMAIN = "uct.ac.za"


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


def account_of(identity: Identity) -> Account:
    email = (identity.email or "").lower()
    if student := STUDENT_EMAIL.fullmatch(email):
        number = student[1].upper()
        return Account(**identity.model_dump(), kind="student", student_number=number)
    # The whole domain must match, so a myuct.ac.za address never passes as staff
    if email.rpartition("@")[2] == STAFF_DOMAIN:
        return Account(**identity.model_dump(), kind="staff")
    raise UctAccountRequired()
