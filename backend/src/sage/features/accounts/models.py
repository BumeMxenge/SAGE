# The body /v1/me answers with, which Finish setup answers with too
from typing import Literal

from pydantic import BaseModel


class Me(BaseModel):
    email: str
    account: Literal["student", "staff"]
    student_number: str | None  # students only
    # False until she finishes setup, and always false for staff
    onboarding_complete: bool
