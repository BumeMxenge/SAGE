# Who is signed in. The frontend routes from this: to onboarding, to the planner, or to the page
# telling staff their side isn't built yet.
from fastapi import APIRouter

from sage.api.deps import SIGNED_IN_ERRORS, SignedIn, Students
from sage.api.models import Me
from sage.api.problems import errors
from sage.domain.accounts import Account

router = APIRouter(tags=["account"])


@router.get(
    "/me",
    summary="Who is signed in, and whether they've finished setup",
    responses=errors(*SIGNED_IN_ERRORS),
)
def get_me(account: SignedIn, students: Students) -> Me:
    profile = students.profile(account.id) if account.kind == "student" else None
    return me(
        account, onboarding_complete=profile is not None and profile.onboarding_complete
    )


def me(account: Account, *, onboarding_complete: bool) -> Me:
    return Me(
        email=account.email,
        account=account.kind,
        student_number=account.student_number,
        onboarding_complete=onboarding_complete,
    )
