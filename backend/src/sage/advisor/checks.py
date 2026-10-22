# What SAGE checks in every reply before it's stored, as E4's score.py checked Luna's: each quote
# against the passage it cites, and the plan it offers against the plans it may offer. A plan id left
# in a reply becomes the plan's name. Two flags mark a reply for a person to read later, and never
# change it. A chat's title has its own check.
import re
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from pydantic import ValidationError

from sage.advisor.evidence import Evidence
from sage.shared.advisor import Reply
from sage.shared.base import Row
from sage.shared.rules import Passage
from sage.shared.students import Citation, Plan

# The one line a reply that gave no checked answer says
REFERRAL = "I couldn't give you a checked answer to this, so please ask your advisor."
REFERRED = Reply(content=REFERRAL, referral=True)
# Limiting words in a kept quote whose loss from the reply can change a condition
CONDITIONS = ("at least", "only", "not", "except", "unless", "minimum", "maximum")
CODE = re.compile(r"\b[A-Z]{3}\d{4}[A-Z]\b")
TIME = re.compile(r"\b\d{1,2}:\d{2}\b")
NUMBER = re.compile(r"\d+(?:\.\d+)?")


class Quote(Row):
    passage_id: str  # a short id, such as P07
    quote: str


class Answer(Row):
    # A reply as Luna gives it, in the reply schema, before the checks
    content: str
    referral: bool
    open_plan_id: str | None
    citations: tuple[Quote, ...]


class Title(Row):
    title: str


class Flag(Row):
    kind: Literal["unsupported_mark", "dropped_condition"]
    mark: str


@dataclass(frozen=True)
class Checked:
    reply: Reply
    dropped: tuple[Quote, ...] = ()  # the quotes the citation check dropped
    unoffered: str | None = None  # a plan offered that she may not be offered
    flags: tuple[Flag, ...] = ()


def check(
    answer: Answer, evidence: Evidence, offerable: Collection[str], heard: str
) -> Checked:
    # The reply she gets from Luna's answer. One that cited the handbook and kept no quote becomes
    # the fixed referral, offering no plan. Otherwise each quote that fails is dropped, and so is a
    # plan she may not be offered: one that turn's find_plan didn't return and the chat isn't on.
    # heard is everything the turn gave Luna besides the slice.
    kept, dropped = quotes_kept(answer.citations, evidence.passages)
    if answer.citations and not kept:
        return Checked(REFERRED, dropped=tuple(dropped))
    content = named(answer.content, evidence.plans)
    offered = answer.open_plan_id
    plan = evidence.plans[offered] if offered in offerable else None
    citations = []
    for position, quote in enumerate(kept, start=1):
        passage = evidence.passages[quote.passage_id]
        citations.append(
            Citation(
                passage_id=passage.id,
                position=position,
                quote=quote.quote,
                source=passage.source,
                section=passage.section,
                page=passage.page,
            )
        )
    return Checked(
        Reply(
            content=content,
            referral=answer.referral,
            open_plan_id=plan.id if plan else None,
            citations=tuple(citations),
        ),
        dropped=tuple(dropped),
        unoffered=offered if offered is not None and plan is None else None,
        flags=tuple(flags(content, kept, heard)),
    )


def named(content: str, plans: Mapping[str, Plan]) -> str:
    # The reply with each of her plans by its name, so she never sees an id: an id followed by its
    # own name loses the id, and any other becomes the name
    for key, plan in plans.items():
        name = re.escape(plan.name)
        content = re.sub(rf"\b{key}\b[,:]?\s*(?:\({name}\)|{name})", plan.name, content)
        content = re.sub(rf"\b{key}\b", plan.name, content)
    return content


def quotes_kept(
    quotes: Sequence[Quote], passages: dict[str, Passage]
) -> tuple[list[Quote], list[Quote]]:
    # The quotes kept and dropped: a quote counts only if it appears word for word in the passage it
    # cites, ignoring line breaks and runs of spaces, as passages keep the PDF's line breaks
    kept, dropped = [], []
    for quote in quotes:
        passage = passages.get(quote.passage_id)
        said = flat(quote.quote)
        found = passage is not None and bool(said) and said in flat(passage.content)
        (kept if found else dropped).append(quote)
    return kept, dropped


def flat(text: str) -> str:
    return " ".join(text.split())


def flags(content: str, kept: Sequence[Quote], heard: str) -> list[Flag]:
    # A course code, time or number the reply holds and no kept quote or anything else Luna heard
    # does, and a limiting word a kept quote holds that the reply leaves out
    evidence = "\n".join([heard, *(quote.quote for quote in kept)])
    found = [
        Flag(kind="unsupported_mark", mark=mark)
        for mark in sorted(marks(content) - marks(evidence))
    ]
    found += [
        Flag(kind="dropped_condition", mark=word)
        for quote in kept
        for word in CONDITIONS
        if holds(quote.quote, word) and not holds(content, word)
    ]
    return found


def marks(text: str) -> set[str]:
    # The course codes, times and other numbers a text holds
    found = set(CODE.findall(text)) | set(TIME.findall(text))
    return found | set(NUMBER.findall(TIME.sub(" ", CODE.sub(" ", text))))


def holds(text: str, mark: str) -> bool:
    # Whether the text holds a word, number or phrase whole, in any case
    pattern = rf"(?<![\w.]){re.escape(mark)}(?!\w)"
    return re.search(pattern, text, re.IGNORECASE) is not None


def checked_title(text: str | None) -> str | None:
    # The chat's title from the title call's reply, or None when it isn't one: 2 to 6 words, at most
    # 40 characters, on one line, with no closing full stop
    try:
        title = Title.model_validate_json(text or "").title.strip()
    except ValidationError:
        return None
    if (
        len(title.splitlines()) != 1
        or not 2 <= len(title.split()) <= 6
        or len(title) > 40
        or title.endswith(".")
    ):
        return None
    return title
