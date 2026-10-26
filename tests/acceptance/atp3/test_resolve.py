# Checks how ATP-3 fixes its expectations, on made-up meetings, plans and passages with every answer
# worked out by hand. None reads prompts.csv or a student, and none calls a model.
from datetime import time
from uuid import uuid4

import pytest
from resolve import (
    PARTS,
    Meeting,
    Unresolved,
    as_meetings,
    day_load,
    expected,
    find_plan,
    finish_after,
    free_days,
    overlaps,
    parse,
    placed,
)
from show_plans import ACCOUNT

from sage.shared.planning import Eligibility
from sage.shared.rules import Passage, TimetableSlot
from sage.shared.students import (
    Plan,
    PlanCourse,
    PlanReason,
    PlanSet,
    Student,
    StudentState,
)


def meeting(code, day, start, end, term="sem1", certain=True):
    return Meeting(
        code=code,
        day=day,
        start=time.fromisoformat(start) if start else None,
        end=time.fromisoformat(end) if end else None,
        parts=PARTS[term],
        certain=certain,
    )


def slot(day, start, end, group=None, choice=None):
    return TimetableSlot(
        id=uuid4(),
        handbook_year=2026,
        course_code="ABC3001F",
        term="sem1",
        day=day,
        start_time=time.fromisoformat(start),
        end_time=time.fromisoformat(end),
        choice_group=group,
        choice=choice,
    )


def test_a_class_ending_on_the_hour_doesnt_finish_after_it():
    # finish_after=16:00: Monday's class ends at 16:00 exactly, Tuesday's a minute later
    week = [
        meeting("ABC1001F", 1, "15:00", "16:00"),
        meeting("ABC1002F", 2, "15:00", "16:01"),
    ]
    assert finish_after(week, time(16, 0))["days"] == ["Tue"]


@pytest.mark.parametrize(
    ("one", "other", "clash"),
    [
        # Touching, then a minute's overlap
        (meeting("A", 1, "10:00", "11:00"), meeting("B", 1, "11:00", "12:00"), False),
        (meeting("A", 1, "10:00", "11:01"), meeting("B", 1, "11:00", "12:00"), True),
        # The same hour on another day
        (meeting("A", 1, "10:00", "11:00"), meeting("B", 2, "10:00", "11:00"), False),
        # The same hour in Q1 and Q2, which share no weeks, then in Q1 and Sem 1, which do
        (
            meeting("A", 1, "10:00", "11:00", "q1"),
            meeting("B", 1, "10:00", "11:00", "q2"),
            False,
        ),
        (
            meeting("A", 1, "10:00", "11:00", "q1"),
            meeting("B", 1, "10:00", "11:00"),
            True,
        ),
        # A meeting with no printed time clashes with nothing
        (meeting("A", 1, None, None), meeting("B", 1, "10:00", "11:00"), False),
    ],
)
def test_meetings_clash_only_when_they_overlap_in_time_and_weeks(one, other, clash):
    assert overlaps(one, other) is clash


def test_a_group_with_two_alternatives_left_is_hers_to_pick_and_one_left_is_fixed():
    # Lab A or B is a choice, and the tutorial's one alternative left is fixed
    found = as_meetings(
        "ABC3001F",
        [
            slot(1, "14:00", "17:00", "lab", "A"),
            slot(3, "14:00", "17:00", "lab", "B"),
            slot(2, "09:00", "10:00", "tutorial", "T1"),
            slot(4, "10:00", "11:00"),
        ],
    )
    assert [m.certain for m in found] == [False, False, True, True]
    # Only an alternative runs past 16:00, so no day is certain
    assert finish_after(found, time(16, 0)) == {
        "days": [],
        "only_as_alternatives": ["Mon", "Wed"],
        "unplaced": [],
    }


def test_a_days_load_goes_in_time_order_with_untimed_meetings_apart():
    week = [
        meeting("ABC1002F", 3, "14:00", "15:00"),
        meeting("ABC1001F", 3, "08:00", "08:45"),
        meeting("ABC1003F", 3, None, None),
        meeting("ABC1004F", 1, "08:00", "08:45"),
    ]
    assert day_load(week, 3) == {
        "day": "Wed",
        "meetings": ["ABC1001F Wed 08:00 to 08:45", "ABC1002F Wed 14:00 to 15:00"],
        "alternatives": [],
        "no_printed_time": ["ABC1003F Wed no printed time"],
        "no_printed_day": [],
    }


def test_a_day_with_only_an_untimed_meeting_isnt_free():
    # Monday has a timed class, Thursday one with no printed time, and Friday only an alternative
    week = [
        meeting("ABC1001F", 1, "08:00", "09:00"),
        meeting("ABC1002F", 4, None, None),
        meeting("ABC1003F", 5, "10:00", "11:00", certain=False),
    ]
    assert free_days(week) == {
        "free": ["Tue", "Wed"],
        "free_unless_she_picks_an_alternative": ["Fri"],
        "no_printed_day": [],
    }


def made_up_set():
    # Three plans: V01 holds A and B, V02 A and C, and V03, hidden, B and C
    student = Student(id=ACCOUNT, curriculum_code="EB000ABC01")
    plan_set = PlanSet(id=uuid4(), student_id=ACCOUNT, period=2026, version=1)
    plans, courses = [], []
    for position, codes, hidden in (
        (1, ("ABC4001F", "ABC4002F"), False),
        (2, ("ABC4001F", "ABC4003F"), False),
        (3, ("ABC4002F", "ABC4003F"), True),
    ):
        plan = Plan(
            id=uuid4(),
            plan_set_id=plan_set.id,
            student_id=ACCOUNT,
            position=position,
            name=f"Plan {position}",
            hidden=hidden,
        )
        plans.append(plan)
        courses += [
            PlanCourse(
                plan_id=plan.id,
                course_code=code,
                student_id=ACCOUNT,
                handbook_year=2026,
            )
            for code in codes
        ]
    reason = PlanReason(
        id=uuid4(),
        plan_set_id=plan_set.id,
        student_id=ACCOUNT,
        kind="conflict",
        message="Every plan takes two of the three.",
    )
    return StudentState(
        student=student,
        plan_sets=(plan_set,),
        plans=tuple(plans),
        plan_courses=tuple(courses),
        plan_reasons=(reason,),
    )


@pytest.mark.parametrize(
    ("have", "avoid", "found"),
    [
        ({"ABC4002F"}, {"ABC4001F"}, ["V03"]),
        ({"ABC4001F"}, set(), ["V01", "V02"]),
        (set(), {"ABC4003F"}, ["V01"]),
    ],
)
def test_find_plan_keeps_hidden_plans_with_every_have_and_no_avoid(have, avoid, found):
    assert [p["plan"] for p in find_plan(made_up_set(), have, avoid)["plans"]] == found


def test_find_plan_with_no_match_gives_the_sets_reasons():
    assert find_plan(made_up_set(), {"ABC4001F", "ABC4002F", "ABC4003F"}, set()) == {
        "plans": [],
        "reasons": ["Every plan takes two of the three."],
    }


def row(**cells):
    return {
        "id": "P01",
        "group": "handbook_plain",
        "expected_behaviour": "answer",
        "quote": "",
        "page": "",
        **cells,
    }


@pytest.mark.parametrize(
    ("status", "behaviour"),
    [("eligible", "answer"), ("check", "refer"), ("not_eligible", "firm_no")],
)
def test_per_engine_follows_the_engines_verdict(status, behaviour):
    found, _ = expected(
        row(expected_behaviour="per_engine"),
        "check_eligibility",
        Eligibility(status=status),
        None,
    )
    assert found == behaviour


def test_a_verdict_against_the_prompts_group_stops_the_run():
    with pytest.raises(Unresolved):
        expected(
            row(group="not_eligible", expected_behaviour="firm_no"),
            "check_eligibility",
            Eligibility(status="eligible"),
            None,
        )
    # A verdict on another group's prompt decides without stopping, as P40's does
    assert expected(
        row(expected_behaviour="per_engine"),
        "check_eligibility",
        Eligibility(status="check"),
        None,
    ) == ("refer", "per_engine: the engine says check")


def passage(content, page=12):
    return Passage(
        id=uuid4(),
        handbook_year=2026,
        source="Handbook",
        section="FB5",
        page=page,
        position=1,
        content=content,
    )


def test_a_quote_outside_her_slice_turns_a_handbook_answer_into_a_referral():
    # Print breaks the line and curls the apostrophe; the quote leaves words out with "..."
    held = passage(
        "A student’s year of study is\nset by the year in which most credits fall."
    )
    prompt = row(quote="A student's year of study ... most credits fall.", page="12")
    in_slice, where = placed(prompt, [held], sliced=set())
    assert (in_slice, where) == (False, "out, page 12")
    assert expected(prompt, "", None, in_slice) == (
        "refer",
        "slice: her slice doesn't hold the quote's passage",
    )
    # The same quote inside her slice stays an answer
    assert placed(prompt, [held], sliced={held.id})[0] is True


def test_a_quote_no_passage_holds_stops_the_run():
    with pytest.raises(Unresolved):
        placed(row(quote="Words print never had."), [passage("Other words.")], set())


@pytest.mark.parametrize(
    "spec",
    [
        "week:sem1:finish_after=4pm",
        "week:term3:free_days",
        "find_plan:has=EEE4120",
        "clash:EEE4120F",
        "check_eligibility:EEE4118F=maybe",
        "find_plan:",
    ],
)
def test_a_spec_it_cant_read_stops_the_run(spec):
    with pytest.raises(Unresolved):
        parse(spec)


def test_a_find_plan_spec_may_leave_one_list_empty():
    assert parse("find_plan:has=EEE4120F;avoid=") == (
        "find_plan",
        {"have": ["EEE4120F"], "avoid": []},
    )
