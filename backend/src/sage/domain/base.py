# The base for every domain type: frozen, so a loaded row can't change under you, and strict about
# keys, so a misspelt column in a seed file is an error rather than silently dropped
from pydantic import BaseModel, ConfigDict


class Row(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
