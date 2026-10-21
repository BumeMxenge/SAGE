# Checks the encoding through the facts it reads, on small years built for each test, with every
# plan worked out by hand: co-requisites and same-year prerequisites met by the plan itself, a year's
# courses and credits met exactly or missed by one, clashes at the edges of their days and terms,
# alternatives, and meetings with no printed time.
from datetime import time
from uuid import uuid4

import pytest

from sage.engine import printed
from sage.engine.evaluator import Record
from sage.engine.facts import Need, Problem, facts, verdicts
from sage.engine.solver import Solver
from sage.shared.rules import (
    TERM_BY_SUFFIX,
    Course,
    CourseNeed,
    EntryRule,
    RuleSet,
    TimetableSlot,
)
from sage.shared.students import Student

STUDENT = Student(curriculum_code="EB000AAA01", id=uuid4(), intake_year=2024)


@pytest.fixture
def symbols(result_symbols):
    return {row.symbol: row for row in result_symbols}


def course(code: str, credits: int = 16, rule: EntryRule | None = None) -> Course:
    # A made-up course, in the term its code's last letter gives
    return Course(
        handbook_year=2026,
        code=code,
        name="Made Up",
        credits=credits,
        nqf_level=7,
        term=TERM_BY_SUFFIX[code[-1]],
        entry_rule=rule,
    )


def meeting(
    code: str,
    day: int | None,
    hours: tuple[time, time] | None,
    term: str | None = None,
    choice: str | None = None,
) -> TimetableSlot:
    return TimetableSlot(
        id=uuid4(),
        handbook_year=2026,
        course_code=code,
        term=term or TERM_BY_SUFFIX[code[-1]],
        day=day,
        start_time=hours[0] if hours else None,
        end_time=hours[1] if hours else None,
        choice_group="lab" if choice else None,
        choice=choice,
    )


def year(courses: list[Course], meetings: tuple | list = ()) -> RuleSet:
    return RuleSet(courses=tuple(courses), timetable_slots=tuple(meetings))


def solve(rules: RuleSet, problem: Problem, symbols) -> list[tuple]:
    # Each plan's courses and its conditional ones, in a fixed order
    record = Record(STUDENT, [], rules, symbols)
    found = Solver().plans(facts(problem, rules, record))
    return sorted((plan.courses, plan.conditional) for plan in found)


def test_a_co_requisite_in_the_same_term_is_met_by_the_plan(symbols):
    alongside = CourseNeed(course="AAA1001S", need="concurrent")
    rules = year([course("AAA2000S", rule=alongside), course("AAA1001S")])
    problem = Problem(required=("AAA2000S", "AAA1001S"))
    assert solve(rules, problem, symbols) == [(("AAA1001S", "AAA2000S"), ())]


@pytest.mark.parametrize(
    ("leaf", "taken", "expected"),
    [
        # A co-requisite starting after its course has started, in the second semester
        (CourseNeed(course="AAA1001S", need="concurrent"), "AAA1001S", "not_met"),
        # A prerequisite in the same semester as its course, so not passed before it starts
        (CourseNeed(course="AAA1001F", need="pass"), "AAA1001F", "not_met"),
    ],
)
def test_the_plan_cant_meet_a_rule_with_a_course_that_comes_too_late(
    leaf, taken, expected, symbols
):
    rules = year([course("AAA2000F", rule=leaf), course(taken)])
    record = Record(STUDENT, [], rules, symbols)
    problem = Problem(required=("AAA2000F", taken))
    assert verdicts(problem, rules, record)["AAA2000F"].value == expected


@pytest.mark.parametrize(
    ("leaf", "conditional"),
    [
        # Passing the first semester's course meets a second-semester prerequisite, as the seed's
        # EEE4022S needs a fourth-year elective
        (CourseNeed(course="AAA1000F", need="pass"), ()),
        # and a pass gives at least 50
        (CourseNeed(course="AAA1000F", need="mark", min_mark=50), ()),
        # but a higher mark is only possible, so its course is conditional, not left out
        (CourseNeed(course="AAA1000F", need="mark", min_mark=51), ("AAA2000S",)),
    ],
)
def test_a_course_the_plan_takes_earlier_in_the_year_meets_a_prerequisite(
    leaf, conditional, symbols
):
    rules = year([course("AAA2000S", rule=leaf), course("AAA1000F")])
    problem = Problem(required=("AAA2000S", "AAA1000F"))
    assert solve(rules, problem, symbols) == [(("AAA1000F", "AAA2000S"), conditional)]


@pytest.mark.parametrize(
    ("amount", "electives"),
    [
        # AAA1001F and AAA1002F make 32 exactly, and AAA1003F would be spare beside them
        (32, ("AAA1001F", "AAA1002F")),
        # 33 needs all three, as any two make 24 or 32
        (33, ("AAA1001F", "AAA1002F", "AAA1003F")),
    ],
)
def test_credits_from_a_group_met_exactly_and_one_short(amount, electives, symbols):
    rules = year(
        [course("AAA1001F"), course("AAA1002F"), course("AAA1003F", credits=8)]
    )
    group = ("AAA1001F", "AAA1002F", "AAA1003F")
    problem = Problem(
        required=(),
        electives=group,
        needs=(Need(kind="credits", amount=amount, courses=group),),
    )
    assert solve(rules, problem, symbols) == [(electives, ())]


@pytest.mark.parametrize(
    ("floor", "courses"),
    [
        # 90 of core and the 16-credit elective make 106 exactly, and the 8-credit one is then spare
        (106, ("AAA1000F", "AAA1001F")),
        # 107 needs both electives, 114
        (107, ("AAA1000F", "AAA1001F", "AAA1002F")),
    ],
)
def test_a_total_met_exactly_and_one_short(floor, courses, symbols):
    rules = year([course("AAA1000F", 90), course("AAA1001F"), course("AAA1002F", 8)])
    problem = Problem(
        required=("AAA1000F",), electives=("AAA1001F", "AAA1002F"), floor=floor
    )
    assert solve(rules, problem, symbols) == [(courses, ())]


@pytest.mark.parametrize(
    ("first", "second", "clash"),
    [
        # Monday, the same term, overlapping by one minute and only touching
        (("AAA1000F", 1, (10, 0), (11, 1)), ("AAA1001F", 1, (11, 0), (12, 0)), True),
        (("AAA1000F", 1, (10, 0), (11, 0)), ("AAA1001F", 1, (11, 0), (12, 0)), False),
        # The same times on another day
        (("AAA1000F", 1, (10, 0), (11, 0)), ("AAA1001F", 2, (10, 0), (11, 0)), False),
        # The first quarter sits inside the first semester, apart from the third quarter, and
        # winter overlaps only itself
        (("AAA1000A", 1, (10, 0), (11, 0)), ("AAA1001F", 1, (10, 0), (11, 0)), True),
        (("AAA1000A", 1, (10, 0), (11, 0)), ("AAA1001C", 1, (10, 0), (11, 0)), False),
        (("AAA1000L", 1, (10, 0), (11, 0)), ("AAA1001F", 1, (10, 0), (11, 0)), False),
    ],
)
def test_two_courses_clash_only_when_their_meetings_overlap(
    first, second, clash, symbols
):
    meetings = [
        meeting(code, day, (time(*start), time(*end)))
        for code, day, start, end in (first, second)
    ]
    codes = (first[0], second[0])
    rules = year([course(code) for code in codes], meetings)
    plans = solve(rules, Problem(required=codes), symbols)
    assert plans == ([] if clash else [(tuple(sorted(codes)), ())])


@pytest.mark.parametrize(
    ("other", "chosen"),
    [
        # A Wednesday course clashing with lab A leaves only lab B
        ("AAA1001F", {"AAA1000F": {"lab": "B"}}),
        # With nothing else on, either lab fits, so neither is chosen for her
        (None, {}),
    ],
)
def test_an_alternative_is_recorded_only_when_the_plan_needs_it(other, chosen, symbols):
    labs = [
        meeting("AAA1000F", 3, (time(14), time(17)), choice="A"),
        meeting("AAA1000F", 5, (time(14), time(17)), choice="B"),
    ]
    courses = [course("AAA1000F")]
    if other:
        labs.append(meeting(other, 3, (time(14), time(16))))
        courses.append(course(other))
    rules = year(courses, labs)
    problem = Problem(required=tuple(c.code for c in courses))
    record = Record(STUDENT, [], rules, symbols)
    written = facts(problem, rules, record)
    solver = Solver()
    (plan,) = solver.plans(written)
    assert solver.choices(written, plan, problem.required) == chosen


@pytest.mark.parametrize(
    ("busy", "found"),
    [
        # AAA1000F takes every afternoon but Friday's, and the two practicals need two days
        ((1, 2, 3, 4), []),
        # It leaves Tuesday and Thursday free, which every way of attending the plan uses
        (
            (1, 3, 5),
            [
                (
                    ("AAA1000F", "CSC3002F"),
                    {"CSC3002F": {"practical": "Tuesday and Thursday"}},
                )
            ],
        ),
    ],
)
def test_csc3002f_needs_two_free_afternoons_for_its_practicals(busy, found, symbols):
    # Its entry (p. 171) prints two 4-hour practicals a week, 14:00 to 18:00, Monday to Friday
    practicals = [
        slot for slot in printed.MEETINGS[2026] if slot.course_code == "CSC3002F"
    ]
    afternoons = [meeting("AAA1000F", day, (time(14), time(15))) for day in busy]
    rules = year([course("CSC3002F", 36), course("AAA1000F")], practicals + afternoons)
    problem = Problem(required=("CSC3002F", "AAA1000F"))
    written = facts(problem, rules, Record(STUDENT, [], rules, symbols))
    solver = Solver()
    plans = solver.plans(written)
    chosen = [
        (plan.courses, solver.choices(written, plan, problem.required))
        for plan in plans
    ]
    assert chosen == found


def test_a_meeting_with_no_printed_time_makes_its_course_conditional(symbols):
    # AAA1001F has a meeting with no day or time; AAA1002F has no meetings at all
    rules = year(
        [course("AAA1001F"), course("AAA1002F")], [meeting("AAA1001F", None, None)]
    )
    problem = Problem(required=("AAA1001F", "AAA1002F"))
    assert solve(rules, problem, symbols) == [(("AAA1001F", "AAA1002F"), ("AAA1001F",))]
