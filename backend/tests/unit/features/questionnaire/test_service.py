# Checks the questionnaire's week question on plans built here, each holding one made-up course with
# the meetings a test gives it: which meetings take the 13:00 lunch hour, and when an option is offered
from datetime import time
from typing import Any
from uuid import UUID, uuid4

import pytest

from sage.features.questionnaire.service import questions
from sage.shared.rules import Course, RuleSet, TimetableSlot, TimetableSlotCurriculum
from sage.shared.students import Plan, PlanCourse, PlanSet, PlanSetRows

STUDENT = UUID(int=1)
HERS, THEIRS = "EB011EEE05", "EB999XYZ99"  # her curriculum, and a made-up second one


def at(start: time | None, end: time | None, **fields: Any) -> dict[str, Any]:
    # A Monday meeting. chosen marks the alternative her plan picked, and only_for links the meeting
    # to one curriculum.
    return {"day": 1, "start_time": start, "end_time": end} | fields


LUNCH_HOUR = at(time(13, 0), time(13, 45))  # a lecture over all of it


def week_options(*plans: list[dict[str, Any]]) -> dict[str, set[int]]:
    # The week question's options for plans with these meetings, each as the positions it keeps
    plan_set = PlanSet(
        id=uuid4(), student_id=STUDENT, period=2026, version=1, complete=True
    )
    rows, plan_courses, courses, slots, links = [], [], [], [], []
    for position, meetings in enumerate(plans, start=1):
        code = f"TST{position:04}F"
        plan = Plan(
            id=uuid4(),
            plan_set_id=plan_set.id,
            student_id=STUDENT,
            position=position,
            name=f"Plan {position}",
        )
        rows.append(plan)
        chosen = {m["choice_group"]: m["choice"] for m in meetings if m.get("chosen")}
        plan_courses.append(
            PlanCourse(
                plan_id=plan.id,
                course_code=code,
                student_id=STUDENT,
                handbook_year=2026,
                choices=chosen or None,
            )
        )
        courses.append(
            Course(
                handbook_year=2026,
                code=code,
                name=f"Test {position}",
                credits=16,
                nqf_level=8,
                term="sem1",
            )
        )
        for meeting in meetings:
            columns = {
                k: v for k, v in meeting.items() if k not in ("chosen", "only_for")
            }
            slot = TimetableSlot(
                id=uuid4(), handbook_year=2026, course_code=code, term="sem1", **columns
            )
            slots.append(slot)
            if "only_for" in meeting:
                links.append(
                    TimetableSlotCurriculum(
                        slot_id=slot.id,
                        handbook_year=2026,
                        curriculum_code=meeting["only_for"],
                    )
                )
    rules = RuleSet(
        courses=tuple(courses),
        timetable_slots=tuple(slots),
        timetable_slot_curricula=tuple(links),
    )
    plan_rows = PlanSetRows(
        plan_set=plan_set, plans=tuple(rows), plan_courses=tuple(plan_courses)
    )
    _, week = questions(plan_rows, rules, HERS, ())
    positions = {plan.id: plan.position for plan in rows}
    return {
        option.id: {positions[plan_id] for plan_id in option.keeps}
        for option in week.options
    }


def tutorials(chosen: str | None) -> list[dict[str, Any]]:
    # Two alternative tutorials, A over lunch and B in the morning, and the one her plan picked
    a = at(
        time(13, 0), time(13, 45), choice_group="tut", choice="A", chosen=chosen == "A"
    )
    b = at(
        time(9, 0), time(9, 45), choice_group="tut", choice="B", chosen=chosen == "B"
    )
    return [a, b]


@pytest.mark.parametrize(
    ("meetings", "free"),
    [
        ([at(time(12, 0), time(13, 0))], True),
        ([at(time(13, 45), time(14, 30))], True),
        ([at(time(12, 0), time(13, 1))], False),
        ([at(time(13, 44), time(14, 30))], False),
        (tutorials(chosen=None), True),
        (tutorials(chosen="A"), False),
        ([at(None, None)], True),
        ([LUNCH_HOUR | {"only_for": THEIRS}], True),
        ([LUNCH_HOUR | {"only_for": HERS}], False),
    ],
    ids=[
        "ends as lunch starts",
        "starts as lunch ends",
        "a minute into lunch",
        "starts a minute before it ends",
        "an alternative she hasn't chosen yet",
        "the alternative she chose",
        "no time printed",
        "another curriculum's meeting",
        "her curriculum's meeting",
    ],
)
def test_lunch_is_free_unless_a_meeting_she_attends_overlaps_it(meetings, free):
    # Plan 1 has the meetings under test, plan 2 a lecture over the whole hour and plan 3 nothing, so
    # the option always narrows the set: to plans 1 and 3, or to plan 3 alone
    options = week_options(meetings, [LUNCH_HOUR], [])
    assert options["lunch_free"] == ({1, 3} if free else {3})


def test_a_week_option_is_offered_only_when_it_keeps_some_plans_but_not_all():
    # Both plans have a lecture over lunch, so keeping the hour free would keep neither
    assert "lunch_free" not in week_options([LUNCH_HOUR], [LUNCH_HOUR])
    # Only plan 2 has one, so the option keeps plan 1 alone
    assert week_options([], [LUNCH_HOUR])["lunch_free"] == {1}
    # Neither has one, so the option would keep both and narrow nothing
    assert "lunch_free" not in week_options([], [])
