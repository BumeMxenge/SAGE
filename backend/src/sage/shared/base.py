# The base for every domain type: frozen, so a loaded row can't change under you, and strict about
# keys, so a misspelt column in a seed file is an error rather than silently dropped. Rows also have
# one written form, for checking a store holds what was written.
import json
from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict


class Row(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


def canonical(rows: Iterable[Row]) -> list[str]:
    # Rows as sorted JSON text, so neither row order nor the key order jsonb stores matters
    return sorted(
        json.dumps(row.model_dump(mode="json"), sort_keys=True) for row in rows
    )
