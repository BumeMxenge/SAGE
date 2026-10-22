# Checks the encoding through the facts it reads, on small years built for each test, with every
# plan worked out by hand: co-requisites and same-year prerequisites met by the plan itself at the
# edges of their terms, rules left open on plan courses, a year's courses and credits met exactly or
# missed by one, clashes at the edges of their days and terms, alternatives, and meetings with no
# printed time.
from datetime import time
from uuid import uuid4

import pytest

from sage.engine.evaluator import Record
from sage.engine.facts import Need, Problem, facts, verdicts
from sage.engine.solver import Solver
from sage.shared.printed_meetings import MEETINGS
from sage.shared.rules import (
    TERM_BY_SUFFIX,
    AllOf,
    AnyOf,
    Course,
    CourseNeed,
    EntryRule,
    Refer,
    RuleSet,
    TimetableSlot,
    TimetableSlotCurriculum,
)
from sage.shared.students import CourseHistoryLine, Student

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


def line(code: str, result: str) -> CourseHistoryLine:
    # One of her 2025 results, in the term its code gives
    return CourseHistoryLine(
        student_id=STUDENT.id,
        academic_year=2025,
        term=TERM_BY_SUFFIX[code[-1]],
        course_code=code,
        course_name="Made Up",
        credits=16,
        result=result,
    )


def solve(rules: RuleSet, problem: Problem, symbols, history=()) -> list[tuple]:
    # Each plan's courses and its conditional ones, in a fixed order
    record = Record(STUDENT, list(history), rules, symbols)
    found = Solver().plans(facts(problem, rules, record))
    return sorted((plan.courses, plan.conditional) for plan in found)


def test_a_co_requisite_in_the_same_term_is_met_by_the_plan(symbols):
    alongside = CourseNeed(course="AAA1001S", need="concurrent")
    rules = year([course("AAA2000S", rule=alongside), course("AAA1001S")])
    problem = Problem(required=("AAA2000S", "AAA1001S"))
    assert solve(rules, problem, symbols) == [(("AAA1001S", "AAA2000S"), ())]


def alongside(code: str) -> CourseNeed:
    return CourseNeed(course=code, need="concurrent")


def before(code: str) -> CourseNeed:
    return CourseNeed(course=code, need="pass")


@pytest.mark.parametrize(
    ("leaf", "owner", "taken", "expected"),
    [
        # A co-requisite in a term that starts as its course's does, one that starts later, and
        # one that starts later inside its course's term (the second quarter)
        (alongside("AAA1001F"), "AAA2000F", "AAA1001F", "open"),
        (alongside("AAA1001S"), "AAA2000F", "AAA1001S", "not_met"),
        (alongside("AAA1001B"), "AAA2000F", "AAA1001B", "not_met"),
        # A prerequisite in a term that ends before its course starts, one in the same term, one
        # in the first quarter, which ends as a first-semester course starts, and one that ends
        # inside a full-year course
        (before("AAA1001F"), "AAA2000S", "AAA1001F", "open"),
        (before("AAA1001F"), "AAA2000F", "AAA1001F", "not_met"),
        (before("AAA1001A"), "AAA2000F", "AAA1001A", "not_met"),
        (before("AAA1001F"), "AAA2000W", "AAA1001F", "not_met"),
        # The plan's other offering of the course, at the same credits
        (before("AAA1001S"), "AAA2000S", "AAA1001F", "open"),
    ],
)
def test_a_plan_course_meets_a_rule_only_when_it_comes_in_time(
    leaf, owner, taken, expected, symbols
):
    codes = dict.fromkeys((owner, taken, leaf.course))
    rules = year([course(code, rule=leaf if code == owner else None) for code in codes])
    record = Record(STUDENT, [], rules, symbols)
    problem = Problem(required=(owner, taken))
    assert verdicts(problem, rules, record)[owner].value == expected


def test_only_a_course_that_covers_a_prerequisite_meets_it(symbols):
    # AAA2000S needs AAA1000F, and the plan takes one of AAA1000F and AAA1001F. AAA1001F comes in
    # time too, but covers nothing AAA2000S needs, so the plan with it can't hold AAA2000S.
    rules = year(
        [
            course("AAA2000S", rule=before("AAA1000F")),
            course("AAA1000F"),
            course("AAA1001F"),
        ]
    )
    group = ("AAA1000F", "AAA1001F")
    problem = Problem(
        required=("AAA2000S",),
        electives=group,
        needs=(Need(kind="courses", amount=1, courses=group),),
    )
    assert solve(rules, problem, symbols) == [(("AAA1000F", "AAA2000S"), ())]


def test_a_rule_left_open_on_two_plan_courses_needs_both(symbols):
    # AAA2000S needs AAA1000F and AAA1001F, and the plan takes two of three electives, so only
    # the plan that takes both can hold it
    both = AllOf(all=(before("AAA1000F"), before("AAA1001F")))
    rules = year(
        [
            course("AAA2000S", rule=both),
            course("AAA1000F"),
            course("AAA1001F"),
            course("AAA1002F"),
        ]
    )
    group = ("AAA1000F", "AAA1001F", "AAA1002F")
    problem = Problem(
        required=("AAA2000S",),
        electives=group,
        needs=(Need(kind="courses", amount=2, courses=group),),
    )
    assert solve(rules, problem, symbols) == [
        (("AAA1000F", "AAA1001F", "AAA2000S"), ())
    ]


def test_a_prerequisite_whose_result_is_still_to_come_leaves_its_course_conditional(
    symbols,
):
    # Her AAA1000F result isn't out, so AAA2000S, which needs it, can be taken on the condition
    # that she passes
    rules = year([course("AAA2000S", rule=before("AAA1000F"))])
    problem = Problem(required=("AAA2000S",))
    history = [line("AAA1000F", "OS")]
    assert solve(rules, problem, symbols, history) == [(("AAA2000S",), ("AAA2000S",))]


def test_a_list_that_words_continue_is_met_through_its_open_branch(symbols):
    # AAA2000S needs AAA1000F, AAA1001F and AAA1002F, "or equivalent". She has passed AAA1000F,
    # and the plan takes the other two earlier in the year, so it meets the rule, and nothing is
    # left for a person to judge.
    branch = AllOf(all=(before("AAA1000F"), before("AAA1001F"), before("AAA1002F")))
    rule = AnyOf(any=(branch, Refer(refer="or equivalent")))
    rules = year(
        [
            course("AAA2000S", rule=rule),
            course("AAA1000F"),
            course("AAA1001F"),
            course("AAA1002F"),
        ]
    )
    problem = Problem(required=("AAA2000S", "AAA1001F", "AAA1002F"))
    assert solve(rules, problem, symbols, [line("AAA1000F", "1")]) == [
        (("AAA1001F", "AAA1002F", "AAA2000S"), ())
    ]


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
        ("AAA1001F", {"AAA1000F": {"lab": ["B"]}}),
        # With nothing else on, either lab fits, so both are left for her to pick from
        (None, {"AAA1000F": {"lab": ["A", "B"]}}),
    ],
)
def test_a_plan_records_every_alternative_that_fits(other, chosen, symbols):
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
        # It leaves Tuesday and Thursday free, the only pair that fits
        (
            (1, 3, 5),
            [
                (
                    ("AAA1000F", "CSC3002F"),
                    {"CSC3002F": {"practical": ["Tuesday and Thursday"]}},
                )
            ],
        ),
        # It leaves Wednesday to Friday free, so any two of those fit, and no pair with Monday
        # or Tuesday
        (
            (1, 2),
            [
                (
                    ("AAA1000F", "CSC3002F"),
                    {
                        "CSC3002F": {
                            "practical": [
                                "Thursday and Friday",
                                "Wednesday and Friday",
                                "Wednesday and Thursday",
                            ]
                        }
                    },
                )
            ],
        ),
    ],
)
def test_csc3002f_lists_only_the_practical_pairs_her_free_afternoons_allow(
    busy, found, symbols
):
    # Its entry (p. 171) prints two 4-hour practicals a week, 14:00 to 18:00, Monday to Friday
    practicals = [slot for slot in MEETINGS[2026] if slot.course_code == "CSC3002F"]
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


def test_a_course_still_clashes_through_its_meetings_after_one_with_no_printed_time(
    symbols,
):
    # AAA1001F's first meeting has no day or time, and its second meets on Monday at 10:00, as
    # AAA1002F's does
    rules = year(
        [course("AAA1001F"), course("AAA1002F")],
        [
            meeting("AAA1001F", None, None),
            meeting("AAA1001F", 1, (time(10), time(11))),
            meeting("AAA1002F", 1, (time(10), time(11))),
        ],
    )
    assert solve(rules, Problem(required=("AAA1001F", "AAA1002F")), symbols) == []


def test_a_meeting_linked_to_her_curriculum_clashes_for_her(symbols):
    # AAA1001F's Monday 10:00 meeting is linked to her curriculum, and AAA1002F meets then too
    linked = meeting("AAA1001F", 1, (time(10), time(11)))
    rules = year(
        [course("AAA1001F"), course("AAA1002F")],
        [linked, meeting("AAA1002F", 1, (time(10), time(11)))],
    ).model_copy(
        update={
            "timetable_slot_curricula": (
                TimetableSlotCurriculum(
                    slot_id=linked.id,
                    handbook_year=2026,
                    curriculum_code=STUDENT.curriculum_code,
                ),
            )
        }
    )
    assert solve(rules, Problem(required=("AAA1001F", "AAA1002F")), symbols) == []
