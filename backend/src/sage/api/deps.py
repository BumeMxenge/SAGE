# What routes ask FastAPI for: the stores the app built at startup, and the sign-in checks. Unit tests
# hand the routes in-memory fakes by overriding the providers.
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sage.domain.accounts import Account, TokenVerifier
from sage.domain.errors import NotSignedIn
from sage.domain.repositories import StudentRepository
from sage.services.accounts import account_of


def verifier(request: Request) -> TokenVerifier:
    return request.app.state.verifier


def students(request: Request) -> StudentRepository:
    return request.app.state.students


Students = Annotated[StudentRepository, Depends(students)]

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
