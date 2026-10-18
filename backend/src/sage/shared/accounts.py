# Which kind of UCT account a verified sign-in is, from its email. A student's address is their
# student number at myuct.ac.za, and staff use uct.ac.za. Nobody else can use SAGE.
import re

from sage.shared.auth import Account, Identity
from sage.shared.errors import UctAccountRequired

STUDENT_EMAIL = re.compile(r"([a-z]{6}[0-9]{3})@myuct\.ac\.za")
STAFF_DOMAIN = "uct.ac.za"


def account_of(identity: Identity) -> Account:
    email = (identity.email or "").lower()
    if student := STUDENT_EMAIL.fullmatch(email):
        number = student[1].upper()
        return Account(**identity.model_dump(), kind="student", student_number=number)
    # The whole domain must match, so a myuct.ac.za address never passes as staff
    if email.rpartition("@")[2] == STAFF_DOMAIN:
        return Account(**identity.model_dump(), kind="staff")
    raise UctAccountRequired()
