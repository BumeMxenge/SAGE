# The chats' bodies: a chat, a message with what it cites, and what she sends to start or ask
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from sage.shared.api.models import RequestBody
from sage.shared.rules import TermCode


class Chat(BaseModel):
    id: UUID
    plan_id: UUID
    # The second plan of a compared pair, stored lowest id first
    other_plan_id: UUID | None
    title: str | None  # null on a new chat, as nothing names one yet
    created_at: datetime


class NewChat(RequestBody):
    plan_id: UUID
    other_plan_id: UUID | None = None  # set to chat about a pair, in either order


class Citation(BaseModel):
    position: int  # its number in the answer
    quote: str
    source: str
    section: str
    page: int


class Message(BaseModel):
    id: UUID
    role: Literal["user", "assistant"]
    content: str
    term: TermCode | None  # the term on screen when she asked
    created_at: datetime
    referral: bool  # the reply hands the question to a human advisor
    open_plan_id: UUID | None  # a plan the reply offers to open
    citations: list[Citation]


class NewMessage(RequestBody):
    content: str = Field(min_length=1, max_length=2000)
    term: TermCode | None = None


class Exchange(BaseModel):
    question: Message
    reply: Message
