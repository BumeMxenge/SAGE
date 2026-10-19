# The interface the advisor will implement. Until it exists, a stand-in in advisor/stubs.py fills it,
# so swapping the real advisor in never touches a route.
from typing import Protocol
from uuid import UUID

from sage.shared.base import Row
from sage.shared.students import Chat, Citation


class Reply(Row):
    content: str
    referral: bool  # it hands the question to a human advisor
    open_plan_id: UUID | None = None  # a plan it offers to open
    citations: tuple[Citation, ...] = ()


class Advisor(Protocol):
    # Answers one question in a chat about a plan, or about a pair of plans
    def reply(self, chat: Chat, question: str, term: str | None) -> Reply: ...
