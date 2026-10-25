# Checks when a plan set needs the questionnaire's narrowing, on rows built here, and the preview of
# a course in a plan's complementary slot: on rows built here for the rule's edges, and on the
# engine's own plan for an ASPECT Mechatronics student for the sections it narrows and fixes
from uuid import UUID, uuid4

import pytest

from sage.engine.generator import ClingoPlanGenerator
from sage.features.plans import service as plans
from sage.features.plans.routes import plan as built
from sage.shared.errors import CourseDoesntFit
from sage.shared.memory.rules import InMemoryRuleRepository
from sage.shared.rulebook import Rulebook
from sage.shared.students import Plan, PlanCourse, PlanReason, PlanSet, PlanSetRows
from scripts.show_plans import on_track

STUDENT = UUID(int=1)


def plan_set(size: int) -> PlanSetRows:
    # A complete set of this many plans, not yet narrowed
    plan_set = PlanSet(
        id=uuid4(), student_id=STUDENT, period=2026, version=1, complete=True
    )
    return PlanSetRows(
        plan_set=plan_set,
        plans=tuple(
            Plan(
                id=uuid4(),
                plan_set_id=plan_set.id,
                student_id=STUDENT,
                position=position,
                name=f"Plan {position}",
            )
            for position in range(1, size + 1)
        ),
    )


# My report's Section 4.1.1: "A questionnaire filters this set when more than five plans exist;
# otherwise the planner opens directly."
@pytest.mark.parametrize(("size", "needed"), [(5, False), (6, True)])
def test_more_than_five_plans_need_the_questionnaire(size, needed):
    assert plans.questionnaire_needed(plan_set(size)) is needed


def details(credits, *fits, forced=None, sections=None):
    # A slot's details as the engine writes them
    return {
        "credits": credits,
        "fits": list(fits),
        "untimed": [],
        "fewer_credits": [],
        "sections": sections or {},
        "forced": forced or {},
    }


def one_plan(*slots: dict, held=()) -> PlanSetRows:
    # A set of one plan, with a reason for each slot's details and a course for each (code, choices)
    rows = plan_set(1)
    (plan,) = rows.plans
    return rows.model_copy(
        update={
            "plan_reasons": tuple(
                PlanReason(
                    id=uuid4(),
                    plan_set_id=plan.plan_set_id,
                    student_id=STUDENT,
                    plan_id=plan.id,
                    kind="included",
                    message="A made-up slot.",
                    details=slot,
                )
                for slot in slots
            ),
            "plan_courses": tuple(
                PlanCourse(
                    plan_id=plan.id,
                    course_code=code,
                    student_id=STUDENT,
                    handbook_year=2026,
                    choices=choices,
                )
                for code, choices in held
            ),
        }
    )


def test_a_course_no_slot_lists_is_refused():
    with pytest.raises(CourseDoesntFit):
        plans.preview(one_plan(details(18, "HST1013F")), "HST1015F")


def test_the_first_slot_that_lists_the_course_is_the_one_it_fills():
    # A line and a place both list it, so the line fills and the place is left
    rows = one_plan(details(18, "HST1013F"), details(8, "HST1013F", "HST1015F"))
    taken, _ = plans.preview(rows, "HST1013F")
    assert [reason.details["credits"] for reason in taken.plan_reasons] == [8]


def test_it_adds_the_course_on_its_sections_and_fixes_only_the_groups_it_forces():
    # The course takes the slot's sections. EEE3096S's lab is fixed to A and its tutorial, which
    # nothing forces, stays as the plan stored it. MEC2045S, with nothing stored, takes its fixed lab
    # alone, and EEE3088F, which nothing forces, stays with none.
    forced = {"HST1013F": {"EEE3096S": {"lab": "A"}, "MEC2045S": {"lab": "B"}}}
    sections = {"HST1013F": {"lecture": ["B"]}}
    rows = one_plan(
        details(18, "HST1013F", forced=forced, sections=sections),
        held=[
            ("EEE3096S", {"lab": ["A", "B"], "tutorial": ["X", "Y"]}),
            ("MEC2045S", None),
            ("EEE3088F", None),
        ],
    )
    taken, fixed = plans.preview(rows, "HST1013F")
    assert {row.course_code: row.choices for row in taken.plan_courses} == {
        "EEE3096S": {"lab": ["A"], "tutorial": ["X", "Y"]},
        "MEC2045S": {"lab": ["B"]},
        "EEE3088F": None,
        "HST1013F": {"lecture": ["B"]},
    }
    assert fixed == [("EEE3096S", "lab", "A"), ("MEC2045S", "lab", "B")]
    # Her own rows are as they were
    assert {row.course_code: row.choices for row in rows.plan_courses}["EEE3096S"] == {
        "lab": ["A", "B"],
        "tutorial": ["X", "Y"],
    }


@pytest.fixture(scope="module")
def aspect(approved_2026, result_symbols):
    # An ASPECT Mechatronics student in her fourth year, on track: the engine's one plan for her,
    # Core Courses Only at 96 credits, which holds EEE3096S with its lab A or B still open
    repository = InMemoryRuleRepository(result_symbols)
    repository.replace_year(approved_2026)
    book = Rulebook(repository)
    rules = book.current()
    student, history = on_track(rules, "EB811EEE05", 4)
    rows = ClingoPlanGenerator().generate(student, history, rules, book.symbols())
    return rows, rules, student.curriculum_code


def week(plan, code):
    # A course's meetings as (day, start, choice), in the order the plan lists them
    (course,) = [course for course in plan.courses if course.code == code]
    return [
        (m.day, m.start_time.strftime("%H:%M") if m.start_time else None, m.choice)
        for m in course.meetings
    ]


def test_a_preview_keeps_the_lecture_that_fits_and_fixes_the_lab_it_forces(aspect):
    # SLL1002S's lectures meet Monday to Wednesday at 12:00 (A) or 16:00 (B). MEC2045S meets Tuesday
    # to Thursday at 12:00, so A clashes and B stays. B's Wednesday 16:00 overlaps EEE3096S's lab B,
    # Wednesday 14:00 to 17:45, so only lab A, Friday 14:00 to 17:45, is left (the 2026 timetable).
    rows, rules, curriculum = aspect
    before = built(rows, rules, curriculum)
    assert week(before, "EEE3096S")[-2:] == [(3, "14:00", "B"), (5, "14:00", "A")]
    taken, forced = plans.preview(rows, "SLL1002S")
    after = built(taken, rules, curriculum)
    assert week(after, "SLL1002S") == [
        (1, "16:00", "B"),
        (2, "16:00", "B"),
        (3, "16:00", "B"),
    ]
    assert week(after, "EEE3096S") == [
        (2, "10:00", None),
        (3, "10:00", None),
        (5, "14:00", "A"),
    ]
    assert forced == [("EEE3096S", "lab", "A")]
    # 96 credits (EEE3088F 8, EEE3091F 16, EEE3092F 16, EEE3096S 16, EEE3099S 8, MEC2045S 16 and
    # MEC2047F 16) and Word Power's 15, with the slot it fills gone
    assert (after.credits.total, after.credits.to_choose) == (111, 0)
    assert after.slots == []
    assert (before.credits.total, before.credits.to_choose) == (96, 18)


def test_a_preview_keeps_a_meeting_with_no_printed_time(aspect):
    # SLL1075F's lectures run Monday to Friday at 08:00 (A) or 13:00 (B), and both fit. Its tutorial
    # and its conversation have no day or time.
    rows, rules, curriculum = aspect
    taken, _ = plans.preview(rows, "SLL1075F")
    meetings = week(built(taken, rules, curriculum), "SLL1075F")
    assert len([m for m in meetings if m[0] is not None]) == 10
    assert [m for m in meetings if m[0] is None] == [(None, None, None)] * 2
