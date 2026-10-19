# The bodies several features share: the base every request body builds on, and a course as the
# catalogue, plans and electives show it. Each feature's own bodies sit in its models.py. All of them
# stay separate from the row types in shared/, so the database can change without the frontend
# noticing, and the other way round.
from pydantic import BaseModel, ConfigDict

from sage.shared.rules import TermCode


class RequestBody(BaseModel):
    # A request body refuses keys it doesn't know, so a misspelt field is an error, not ignored
    model_config = ConfigDict(extra="forbid")


class Course(BaseModel):
    code: str
    name: str
    credits: int
    term: TermCode
