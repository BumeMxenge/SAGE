# What routes ask FastAPI for: the stores the app built at startup, and the sign-in checks. Unit tests
# hand the routes in-memory fakes by overriding the providers.
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sage.domain.accounts import Account, TokenVerifier
from sage.domain.errors import NotSignedIn, StudentsOnly, UctAccountRequired
from sage.domain.planning import PlanGenerator
from sage.domain.repositories import StudentRepository
from sage.services.accounts import account_of
from sage.services.rulebook import Rulebook


def verifier(request: Request) -> TokenVerifier:
    return request.app.state.verifier


def students(request: Request) -> StudentRepository:
    return request.app.state.students


def rulebook(request: Request) -> Rulebook:
    return request.app.state.rulebook


def plan_generator(request: Request) -> PlanGenerator:
    return request.app.state.plan_generator


Students = Annotated[StudentRepository, Depends(students)]
Rules = Annotated[Rulebook, Depends(rulebook)]
Generator = Annotated[PlanGenerator, Depends(plan_generator)]

# With auto_error off, a missing token becomes the not_signed_in problem rather than FastAPI's own
# error. It also gives /docs its Authorize button.
bearer = HTTPBearer(auto_error=False)


def signed_in(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    tokens: Annotated[TokenVerifier, Depends(verifier)],
) -> Account:
    if credentials is None:
        raise NotSignedIn()
    return account_of(tokens.verify(credentials.credentials))


SignedIn = Annotated[Account, Depends(signed_in)]


def student_account(account: SignedIn) -> Account:
    if account.kind != "student":
        raise StudentsOnly()
    return account


StudentAccount = Annotated[Account, Depends(student_account)]

# The refusals each guard can raise, for the routes' declared errors
SIGNED_IN_ERRORS = (NotSignedIn, UctAccountRequired)
STUDENT_ERRORS = (*SIGNED_IN_ERRORS, StudentsOnly)
