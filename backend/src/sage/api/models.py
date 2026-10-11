# The API's contract: every request and response body. These stay separate from the domain's row
# types, so the database can change without the frontend noticing, and the other way round.
from typing import Literal

from pydantic import BaseModel


class Health(BaseModel):
    status: Literal["ok"]
    commit: str  # the commit the image was built from; "dev" on a laptop


class Me(BaseModel):
    email: str
    name: str | None
    account: Literal["student", "staff"]
    student_number: str | None  # students only
    onboarding_complete: (
        bool  # false until she finishes setup, and always false for staff
    )
