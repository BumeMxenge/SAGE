# The body /health answers with
from typing import Literal

from pydantic import BaseModel


class Health(BaseModel):
    status: Literal["ok"]
    commit: str  # the commit the image was built from; "dev" on a laptop
