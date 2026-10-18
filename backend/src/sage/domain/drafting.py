# The interface a model that drafts rule trees implements. Ingestion depends only on this, so the
# provider behind it can change in one adapter, and tests use a fake that never calls a model.
from typing import Literal, Protocol

from pydantic import JsonValue


class Drafter(Protocol):
    model: str  # the model's name, kept with each of its drafts

    # A rule tree, as JSON, for printed wording the grammar refused. A co-requisite's leaves need the
    # course taken alongside, the rest a pass.
    def draft(self, printed: str, need: Literal["pass", "concurrent"]) -> JsonValue: ...
