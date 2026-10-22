# What the advisor's tests share: the evidence for a question in a chat on Mbali's seeded plans,
# against the approved 2026, with the engine's eligibility checker
from collections.abc import Callable
from uuid import uuid4

import pytest

from sage.advisor.evidence import Evidence
from sage.engine.eligibility import EntryRuleEligibility
from sage.shared.rulebook import Rulebook
from sage.shared.students import Chat
from tests.unit.accounts import MBALI


@pytest.fixture
def chat_on(stores) -> Callable[..., Chat]:
    # A new chat of hers on the plans at these positions, one or a pair, stored lowest id first. It
    # has a title unless a test says otherwise, so only the tests of titles ask for one.
    students = stores[1]

    def on(*positions: int, title: str | None = "Made-Up Title") -> Chat:
        plans = {plan.position: plan.id for plan in students.get(MBALI).plans}
        first, *other = sorted(plans[position] for position in positions)
        return students.add_chat(
            Chat(
                id=uuid4(),
                student_id=MBALI,
                plan_id=first,
                other_plan_id=other[0] if other else None,
                title=title,
            )
        )

    return on


@pytest.fixture
def evidence(stores, chat_on) -> Callable[[], Evidence]:
    # What Luna is given for a question in a chat on her first plan
    rules, students = stores

    def build() -> Evidence:
        return Evidence(
            chat_on(1), "sem1", students, Rulebook(rules), EntryRuleEligibility()
        )

    return build
