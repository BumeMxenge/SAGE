# A complementary slot as the engine stores it, in its plan's reason: a line of the year's
# complementary credits, or a 576-credit place standing in for a course she still owes. The reason's
# details hold the approved courses that fit the plan's timetable, those with a meeting that has no
# printed time or fewer credits than the line, the sections of each that fit, and any section of the
# plan's own courses one forces. Only a slot's reason has details. Plans and electives both read them.
from collections.abc import Iterable
from uuid import UUID

from sage.shared.base import Row
from sage.shared.students import PlanReason


class PlanSlot(Row):
    plan_id: UUID
    message: str  # the reason's words
    credits: int
    fits: tuple[str, ...]
    untimed: tuple[str, ...]
    fewer_credits: tuple[str, ...]
    # Each fitting course's sections that fit, by choice group, and the section of each of the plan's
    # courses it forces, by course and choice group
    sections: dict[str, dict[str, list[str]]]
    forced: dict[str, dict[str, dict[str, str]]]
    owed: str | None = None  # the course a 576-credit place stands in for


def plan_slots(reasons: Iterable[PlanReason]) -> list[PlanSlot]:
    return [
        PlanSlot(plan_id=reason.plan_id, message=reason.message, **reason.details)
        for reason in reasons
        if reason.details
    ]
