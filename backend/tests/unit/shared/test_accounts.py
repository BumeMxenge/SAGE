# Checks how an email decides the kind of account, including addresses made to slip past the rule
from uuid import UUID

import pytest

from sage.shared.accounts import account_of
from sage.shared.auth import Identity
from sage.shared.errors import UctAccountRequired


def identity(email: str | None) -> Identity:
    return Identity(id=UUID(int=1), email=email)


@pytest.mark.parametrize(
    ("email", "kind", "number"),
    [
        ("dlmmba999@myuct.ac.za", "student", "DLMMBA999"),
        ("DLMMBA999@MyUCT.ac.za", "student", "DLMMBA999"),
        ("test.advisor@uct.ac.za", "staff", None),
    ],
)
def test_uct_accounts(email, kind, number):
    account = account_of(identity(email))
    assert (account.kind, account.student_number) == (kind, number)


@pytest.mark.parametrize(
    "email",
    [
        None,
        "outsider@example.com",
        "dlmmba99@myuct.ac.za",  # too few digits
        "dlmmba9999@myuct.ac.za",  # too many
        "test.advisor@myuct.ac.za",  # the student domain without a student number
        "dlmmba999@myuct.ac.za.example.com",
        "someone@notuct.ac.za",
    ],
)
def test_everyone_else_is_refused(email):
    with pytest.raises(UctAccountRequired):
        account_of(identity(email))
