# The interface the advisor fills, in advisor/replies.py, so the routes never depend on it directly
from typing import Protocol
from uuid import UUID

from sage.shared.base import Row
from sage.shared.students import Chat, Citation


class Reply(Row):
    content: str
    referral: bool  # it hands the question to a human advisor
    open_plan_id: UUID | None = None  # a plan it offers to open
    citations: tuple[Citation, ...] = ()
    title: str | None = None  # a name for a chat that has none yet


class Advisor(Protocol):
    # Answers one question in a chat about a plan, or about a pair of plans
    def reply(self, chat: Chat, question: str, term: str | None) -> Reply: ...
