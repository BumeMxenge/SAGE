# Who is signed in. The frontend routes from this: to onboarding, to the planner, or to the page
# telling staff their side isn't built yet.
from fastapi import APIRouter

from sage.api.deps import SignedIn, Students
from sage.api.models import Me
from sage.api.problems import errors
from sage.domain.errors import NotSignedIn, UctAccountRequired

router = APIRouter(tags=["account"])


@router.get(
    "/me",
    summary="Who is signed in, and whether they've finished setup",
    responses=errors(NotSignedIn, UctAccountRequired),
)
def get_me(account: SignedIn, students: Students) -> Me:
    profile = students.profile(account.id) if account.kind == "student" else None
    return Me(
        email=account.email,
        name=account.name,
        account=account.kind,
        student_number=account.student_number,
        onboarding_complete=profile is not None and profile.onboarding_complete,
    )
