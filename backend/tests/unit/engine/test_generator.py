# Checks the plan sets the generator builds, on small years made up for each test with every plan,
# reason and cited passage worked out by hand, and on Mbali's own record against the approved
# 2026, whose plans must be her seed's 10, written by hand from print
from collections import Counter
from datetime import time
from uuid import UUID, uuid4

import pytest

from sage.engine.generator import ClingoPlanGenerator, combination, name
from sage.shared.printed_meetings import timetabled
from sage.shared.rules import (
    TERM_BY_SUFFIX,
    AllOfGroup,
    AnyOf,
    ChooseFromGroup,
    Course,
    CourseGroup,
    CourseGroupMember,
    CourseNeed,
    CreditsFromGroups,
    CurriculumRule,
    HandbookVersion,
    Passage,
    Refer,
    RuleSet,
    TimetableSlot,
    TotalCredits,
    YearRules,
)
from sage.shared.seed import load_seed
from sage.shared.students import CourseHistoryLine, PlanSetRows, Student

STUDENT = UUID(int=7)
CURRICULUM = "EB000AAA01"


@pytest.fixture
def symbols(result_symbols):
    return {row.symbol: row for row in result_symbols}


def course(code: str, credits: int = 16, rule=None) -> Course:
    return Course(
        handbook_year=2026,
        code=code,
        name=f"Course {code}",
        credits=credits,
        nqf_level=7,
        term=TERM_BY_SUFFIX[code[-1]],
        entry_rule=rule,
    )


def meeting(
    code: str,
    day: int | None,
    start: int | None = None,
    section: tuple[str, str] | None = None,
) -> TimetableSlot:
    # An hour from the given hour, or a meeting with no printed day or time, and the choice group
    # and alternative of a section
    group, choice = section or (None, None)
    return TimetableSlot(
        id=uuid4(),
        handbook_year=2026,
        course_code=code,
        term=TERM_BY_SUFFIX[code[-1]],
        day=day,
        start_time=time(start) if start else None,
        end_time=time(start + 1) if start else None,
        choice_group=group,
        choice=choice,
    )


def rulebook(
    years: dict[int, tuple],
    groups: dict[str, tuple[str, ...]],
    courses: list[Course],
    meetings: list[TimetableSlot] | None = None,
    curriculum: str = CURRICULUM,
) -> RuleSet:
    # A made-up year of rules for one curriculum: each year's rules, its groups and their courses
    return RuleSet(
        handbook_versions=(HandbookVersion(year=2026, approved=True),),
        curriculum_rules=tuple(
            CurriculumRule(
                handbook_year=2026,
                curriculum_code=curriculum,
                year_of_study=number,
                rule=YearRules(all=parts),
            )
            for number, parts in years.items()
        ),
        courses=tuple(courses),
        course_groups=tuple(
            CourseGroup(handbook_year=2026, group_key=key, label=key) for key in groups
        ),
        course_group_members=tuple(
            CourseGroupMember(handbook_year=2026, group_key=key, course_code=code)
            for key, codes in groups.items()
            for code in codes
        ),
        timetable_slots=tuple(meetings or ()),
    )


def core(group: str) -> AllOfGroup:
    return AllOfGroup(all_of_group=group)


def total(credits: int) -> TotalCredits:
    return TotalCredits(total_credits=credits)


def line(code: str, result: str = "1", credits: int = 16) -> CourseHistoryLine:
    return CourseHistoryLine(
        student_id=STUDENT,
        academic_year=2025,
        term=TERM_BY_SUFFIX[code[-1]],
        course_code=code,
        course_name=f"Course {code}",
        credits=credits,
        result=result,
    )


def generate(
    rules: RuleSet,
    symbols,
    history: tuple = (),
    intake: int = 2025,
    curriculum: str = CURRICULUM,
) -> PlanSetRows:
    student = Student(id=STUDENT, curriculum_code=curriculum, intake_year=intake)
    return ClingoPlanGenerator().generate(student, list(history), rules, symbols)


def plans(rows: PlanSetRows) -> list[tuple[str, ...]]:
    # Each plan's courses, best first
    return [
        tuple(sorted(c.course_code for c in rows.plan_courses if c.plan_id == plan.id))
        for plan in sorted(rows.plans, key=lambda plan: plan.position)
    ]


def messages(rows: PlanSetRows, kind: str) -> list[str]:
    return [reason.message for reason in rows.plan_reasons if reason.kind == kind]


def passage(
    section: str,
    curriculum: str | None = None,
    course: str | None = None,
    position: int = 0,
) -> Passage:
    # A made-up passage: one of a curriculum's tables, a course's own entry, or a faculty rule
    return Passage(
        id=uuid4(),
        handbook_year=2026,
        curriculum_code=curriculum,
        course_code=course,
        source="Made-up handbook",
        section=section,
        page=1,
        position=position,
        content=section,
    )


def cited(rules: RuleSet, rows: PlanSetRows) -> Counter:
    # Each reason by whether it's the set's, its kind and course, and the curriculum and section
    # of the passage it cites
    found = {p.id: (p.curriculum_code, p.section) for p in rules.passages}
    return Counter(
        (r.plan_id is None, r.kind, r.course_code, found.get(r.passage_id))
        for r in rows.plan_reasons
    )


def test_choose_two_of_three_gives_three_plans_with_none_to_spare(symbols):
    rules = rulebook(
        {1: (core("y1"), ChooseFromGroup(choose=2, from_group="g"), total(48))},
        {"y1": ("AAA1000F",), "g": ("AAA1001F", "AAA1002F", "AAA1003F")},
        [course(code) for code in ("AAA1000F", "AAA1001F", "AAA1002F", "AAA1003F")],
    )
    rows = generate(rules, symbols)
    # Each pair of the three, beside the core; all three would leave one spare
    assert sorted(plans(rows)) == [
        ("AAA1000F", "AAA1001F", "AAA1002F"),
        ("AAA1000F", "AAA1001F", "AAA1003F"),
        ("AAA1000F", "AAA1002F", "AAA1003F"),
    ]
    assert messages(rows, "excluded") == [
        (
            "Plans with more electives than the rules ask for aren't listed. The handbook "
            "allows more, so ask your advisor if you want to add one."
        )
    ]


TWO = ChooseFromGroup(choose=2, from_group="g")
ONE_MORE = [("AAA1000F", "AAA1002F"), ("AAA1000F", "AAA1003F")]


@pytest.mark.parametrize(
    ("part", "done", "expected", "asked"),
    [
        # She took AAA1001F early, so choosing 2 of the three leaves 1 more, and her year's 48
        # drops by its 16 to 32, which the core and one more make
        (TWO, (line("AAA1001F"),), ONE_MORE, ["at least 1 of AAA1002F and AAA1003F"]),
        # A result still to come counts the same, and that course isn't offered again
        (
            TWO,
            (line("AAA1001F", "OS"),),
            ONE_MORE,
            ["at least 1 of AAA1002F and AAA1003F"],
        ),
        # 32 credits from the group leave 16 after her 16
        (
            CreditsFromGroups(credits=32, from_groups=("g",)),
            (line("AAA1001F"),),
            ONE_MORE,
            ["at least 16 credits from AAA1002F and AAA1003F"],
        ),
        # Two passed leave nothing to ask, and the core alone makes the 16 left of her year
        (TWO, (line("AAA1001F"), line("AAA1002F")), [("AAA1000F",)], []),
    ],
)
def test_a_course_she_has_done_in_a_group_counts_towards_its_rule(
    part, done, expected, asked, symbols
):
    rules = rulebook(
        {1: (core("y1"), part, total(48))},
        {"y1": ("AAA1000F",), "g": ("AAA1001F", "AAA1002F", "AAA1003F")},
        [course(code) for code in ("AAA1000F", "AAA1001F", "AAA1002F", "AAA1003F")],
    )
    rows = generate(rules, symbols, done)
    assert sorted(plans(rows)) == expected
    takes = [m for m in messages(rows, "included") if m.startswith("Every plan takes")]
    assert takes == [f"Every plan takes {words}." for words in asked]


def test_a_core_course_she_still_owes_from_an_earlier_year_is_in_every_plan(symbols):
    # She passed her second year's core but not her first's, so she's in her third year and owes
    # AAA1000F from her first
    rules = rulebook(
        {
            1: (core("y1"), total(16)),
            2: (core("y2"), total(32)),
            3: (core("y3"), ChooseFromGroup(choose=1, from_group="g"), total(32)),
        },
        {
            "y1": ("AAA1000F",),
            "y2": ("AAA2000F", "AAA2001F"),
            "y3": ("AAA3000S",),
            "g": ("AAA3001S", "AAA3002S"),
        },
        [
            course(code)
            for code in (
                "AAA1000F",
                "AAA2000F",
                "AAA2001F",
                "AAA3000S",
                "AAA3001S",
                "AAA3002S",
            )
        ],
    )
    history = (line("AAA1000F", "F"), line("AAA2000F"), line("AAA2001F"))
    rows = generate(rules, symbols, history)
    assert sorted(plans(rows)) == [
        ("AAA1000F", "AAA3000S", "AAA3001S"),
        ("AAA1000F", "AAA3000S", "AAA3002S"),
    ]


def test_a_course_she_owes_from_an_earlier_year_beats_a_clashing_current_one(symbols):
    # She passed her second year and owes AAA1000F from her first, which meets on Monday at 10:00,
    # as her third year's AAA3000F does, so AAA3000F gives way (FB3.4)
    rules = rulebook(
        {
            1: (core("y1"), total(16)),
            2: (core("y2"), total(32)),
            3: (core("y3"), total(32)),
        },
        {
            "y1": ("AAA1000F",),
            "y2": ("AAA2000F", "AAA2001F"),
            "y3": ("AAA3000F", "AAA3001F"),
        },
        [
            course(code)
            for code in ("AAA1000F", "AAA2000F", "AAA2001F", "AAA3000F", "AAA3001F")
        ],
        [
            meeting("AAA1000F", 1, 10),
            meeting("AAA3000F", 1, 10),
            meeting("AAA3001F", 2, 10),
        ],
    )
    history = (line("AAA1000F", "F"), line("AAA2000F"), line("AAA2001F"))
    rows = generate(rules, symbols, history)
    assert plans(rows) == [("AAA1000F", "AAA3001F")]
    (conflict,) = [r for r in rows.plan_reasons if r.kind == "conflict"]
    assert (conflict.course_code, conflict.plan_id, conflict.message) == (
        "AAA3000F",
        None,
        (
            "AAA3000F clashes with AAA1000F, which you still owe from an earlier year. A "
            "course you still owe from an earlier year comes first, so AAA3000F isn't in your "
            "plans. See your advisor about it."
        ),
    )


def test_a_course_she_is_repeating_beats_a_clashing_current_one(symbols):
    # She failed AAA2000F last year and repeats it in her second year, and AAA2001F meets with it
    # on Monday at 10:00, so AAA2001F gives way (FB3.4)
    rules = rulebook(
        {1: (core("y1"), total(32)), 2: (core("y2"), total(48))},
        {"y1": ("AAA1000F", "AAA1001F"), "y2": ("AAA2000F", "AAA2001F", "AAA2002F")},
        [
            course(code)
            for code in ("AAA1000F", "AAA1001F", "AAA2000F", "AAA2001F", "AAA2002F")
        ],
        [
            meeting("AAA2000F", 1, 10),
            meeting("AAA2001F", 1, 10),
            meeting("AAA2002F", 2, 10),
        ],
    )
    history = (line("AAA1000F"), line("AAA1001F"), line("AAA2000F", "F"))
    rows = generate(rules, symbols, history)
    assert plans(rows) == [("AAA2000F", "AAA2002F")]
    (conflict,) = [r for r in rows.plan_reasons if r.kind == "conflict"]
    assert (conflict.course_code, conflict.message) == (
        "AAA2001F",
        (
            "AAA2001F clashes with AAA2000F, which you're repeating. A course you're "
            "repeating comes first, so AAA2001F isn't in your plans. See your advisor about it."
        ),
    )


def test_two_current_core_courses_that_clash_leave_no_plan_and_say_why(symbols):
    rules = rulebook(
        {1: (core("y1"), total(32))},
        {"y1": ("AAA1000F", "AAA1001F")},
        [course("AAA1000F"), course("AAA1001F")],
        [meeting("AAA1000F", 1, 10), meeting("AAA1001F", 1, 10)],
    ).model_copy(update={"passages": (passage("y1", CURRICULUM), passage("FB3.4"))})
    rows = generate(rules, symbols)
    assert rows.plans == ()
    assert messages(rows, "conflict") == [
        "No plan can hold AAA1000F and AAA1001F together, so see your advisor."
    ]
    # Courses that only clash rest on FB3.4
    assert cited(rules, rows)[(True, "conflict", None, (None, "FB3.4"))] == 1


def test_a_year_rule_no_plan_can_meet_is_named_with_its_table(symbols):
    # She must take both of AAA1001F and AAA1002F, which meet together on Monday at 10:00
    rules = rulebook(
        {1: (core("y1"), ChooseFromGroup(choose=2, from_group="g"), total(16))},
        {"y1": ("AAA1000F",), "g": ("AAA1001F", "AAA1002F")},
        [course(code) for code in ("AAA1000F", "AAA1001F", "AAA1002F")],
        [meeting("AAA1001F", 1, 10), meeting("AAA1002F", 1, 10)],
    ).model_copy(
        update={
            "passages": (
                passage("y1", CURRICULUM),
                passage("g", CURRICULUM, position=1),
                passage("FB3.4"),
            )
        }
    )
    rows = generate(rules, symbols)
    assert rows.plans == ()
    assert messages(rows, "conflict") == [
        "No plan can hold at least 2 of AAA1001F and AAA1002F together, so see your advisor."
    ]
    assert cited(rules, rows)[(True, "conflict", None, (CURRICULUM, "g"))] == 1


def test_a_minimum_no_plan_can_reach_is_named_with_its_table(symbols):
    # Her year's 64 credits, when its core and both electives make only 48
    rules = rulebook(
        {1: (core("y1"), ChooseFromGroup(choose=1, from_group="g"), total(64))},
        {"y1": ("AAA1000F",), "g": ("AAA1001F", "AAA1002F")},
        [course(code) for code in ("AAA1000F", "AAA1001F", "AAA1002F")],
    ).model_copy(
        update={
            "passages": (
                passage("y1", CURRICULUM),
                passage("g", CURRICULUM, position=1),
            )
        }
    )
    rows = generate(rules, symbols)
    assert rows.plans == ()
    assert messages(rows, "conflict") == [
        "No plan can hold at least 64 credits together, so see your advisor."
    ]
    # The year's last table prints its total
    assert cited(rules, rows)[(True, "conflict", None, (CURRICULUM, "g"))] == 1


def test_a_rule_a_plan_meets_and_one_a_person_must_judge_each_get_their_reason(
    symbols,
):
    # AAA1003S needs AAA1000F, which every plan takes in the first semester. Of the electives,
    # AAA1001F needs a person's judgement, so its plan holds it on that condition, and AAA1002F
    # needs AAA1000F alongside "or equivalent", which only its own plan holds.
    alongside = CourseNeed(course="AAA1000F", need="concurrent")
    rules = rulebook(
        {1: (core("y1"), ChooseFromGroup(choose=1, from_group="g"), total(48))},
        {"y1": ("AAA1000F", "AAA1003S"), "g": ("AAA1001F", "AAA1002F")},
        [
            course("AAA1000F"),
            course("AAA1003S", rule=CourseNeed(course="AAA1000F", need="pass")),
            course("AAA1001F", rule=Refer(refer="By permission of the convener.")),
            course(
                "AAA1002F", rule=AnyOf(any=(alongside, Refer(refer="or equivalent")))
            ),
        ],
    ).model_copy(
        update={
            "passages": tuple(
                passage(f"{code} entry", course=code)
                for code in ("AAA1001F", "AAA1002F", "AAA1003S")
            )
        }
    )
    rows = generate(rules, symbols)
    assert "Every plan comes to at least 48 credits for the year." in messages(
        rows, "included"
    )
    holding = {
        plan.id: tuple(
            sorted(c.course_code for c in rows.plan_courses if c.plan_id == plan.id)
        )
        for plan in rows.plans
    }
    sections = {p.id: p.section for p in rules.passages}
    said = {
        (holding.get(r.plan_id), r.kind, r.message, sections[r.passage_id])
        for r in rows.plan_reasons
        if r.course_code in ("AAA1001F", "AAA1002F", "AAA1003S")
    }
    assert said == {
        (
            None,
            "included",
            "AAA1003S needs AAA1000F, which every plan holds in time.",
            "AAA1003S entry",
        ),
        (
            ("AAA1000F", "AAA1001F", "AAA1003S"),
            "conditional",
            (
                'AAA1001F needs "By permission of the convener." SAGE can\'t check this, so '
                "confirm it with your advisor."
            ),
            "AAA1001F entry",
        ),
        (
            ("AAA1000F", "AAA1002F", "AAA1003S"),
            "included",
            (
                'AAA1002F needs AAA1000F taken alongside "or equivalent", which this plan '
                "holds in time."
            ),
            "AAA1002F entry",
        ),
    }


def test_a_core_course_she_cant_take_yet_is_left_out_and_her_minimum_drops(symbols):
    # AAA1001F needs ZZZ1000F, which she hasn't passed. Without it her year's 80 drops by its 32 to
    # 48, which AAA1000F and two of the three electives make. Had AAA1000F's 16 come off in its
    # place she'd need all three, and had both come off, one.
    rules = rulebook(
        {
            1: (
                core("y1"),
                CreditsFromGroups(credits=16, from_groups=("g",)),
                total(80),
            )
        },
        {"y1": ("AAA1000F", "AAA1001F"), "g": ("AAA1002F", "AAA1003F", "AAA1004F")},
        [
            course("AAA1000F"),
            course("AAA1001F", 32, rule=CourseNeed(course="ZZZ1000F", need="pass")),
            course("AAA1002F"),
            course("AAA1003F"),
            course("AAA1004F"),
        ],
    )
    rows = generate(rules, symbols)
    assert sorted(plans(rows)) == [
        ("AAA1000F", "AAA1002F", "AAA1003F"),
        ("AAA1000F", "AAA1002F", "AAA1004F"),
        ("AAA1000F", "AAA1003F", "AAA1004F"),
    ]
    assert messages(rows, "excluded")[-1] == (
        "AAA1001F isn't in your plans, as it needs ZZZ1000F, which your record doesn't show "
        "yet. Your year is now under its printed minimum of 80 credits, and your advisor can "
        "give permission for that."
    )


def test_complementary_credits_she_has_met_come_off_her_minimum(symbols):
    # Her first year's KKK1000F already meets its 18 complementary credits, so her year's 50 drops
    # by AAA1000F's 16 and those 18 to 16, which AAA1001F makes. Had the 18 stayed, she'd need 34.
    rules = rulebook(
        {
            1: (
                core("y1"),
                CreditsFromGroups(credits=18, from_groups=("complementary",)),
                total(50),
            )
        },
        {"y1": ("AAA1000F", "AAA1001F"), "complementary": ("KKK1000F",)},
        [course("AAA1000F"), course("AAA1001F"), course("KKK1000F", 18)],
    )
    history = (line("AAA1000F"), line("KKK1000F", credits=18))
    assert plans(generate(rules, symbols, history)) == [("AAA1001F",)]


def test_a_slot_lists_the_complementary_courses_that_fit_marking_untimed_ones(symbols):
    # AAA1000F meets on Monday at 10:00. KKK1000F clashes with it, KKK1001F has no printed time
    # and KKK1002F meets on Tuesday. KKK1003F needs a course she hasn't passed, so it isn't
    # listed, while KKK1004F, which a person must judge, is (Stop 1's decision 17).
    complementary = ("KKK1000F", "KKK1001F", "KKK1002F", "KKK1003F", "KKK1004F")
    rules = rulebook(
        {
            1: (
                core("y1"),
                CreditsFromGroups(credits=18, from_groups=("complementary",)),
                total(34),
            )
        },
        {"y1": ("AAA1000F",), "complementary": complementary},
        [course("AAA1000F")]
        + [course(c, 18) for c in ("KKK1000F", "KKK1001F", "KKK1002F")]
        + [
            course("KKK1003F", 18, CourseNeed(course="ZZZ1000F", need="pass")),
            course("KKK1004F", 18, Refer(refer="By permission of the convener.")),
        ],
        [
            meeting("AAA1000F", 1, 10),
            meeting("KKK1000F", 1, 10),
            meeting("KKK1001F", None),
            meeting("KKK1002F", 2, 10),
            meeting("KKK1003F", 2, 11),
            meeting("KKK1004F", 2, 12),
        ],
    )
    rows = generate(rules, symbols)
    (slot,) = [r for r in rows.plan_reasons if r.details]
    assert (slot.kind, slot.course_code, slot.details) == (
        "included",
        None,
        {
            "credits": 18,
            "fits": ["KKK1001F", "KKK1002F", "KKK1004F"],
            "untimed": ["KKK1001F"],
            "fewer_credits": [],
            "sections": {},
            "forced": {},
        },
    )


def test_a_15_credit_course_fills_an_18_credit_line_and_needs_a_check(symbols):
    # One approved course fills a line, as pp. 42 and 44 ask for "at least one course from a list
    # of approved electives", so her first year's 15-credit KKK1000F leaves nothing of its 18 for
    # her second year. There, the 15-credit KKK1001F is listed as needing a check.
    line_of_18 = CreditsFromGroups(credits=18, from_groups=("complementary",))
    rules = rulebook(
        {
            1: (core("y1"), line_of_18, total(34)),
            2: (core("y2"), line_of_18, total(34)),
        },
        {
            "y1": ("AAA1000F",),
            "y2": ("AAA2000F",),
            "complementary": ("KKK1000F", "KKK1001F", "KKK1002F"),
        },
        [course("AAA1000F"), course("AAA2000F")]
        + [course("KKK1000F", 15), course("KKK1001F", 15), course("KKK1002F", 18)],
    )
    rows = generate(rules, symbols, (line("AAA1000F"), line("KKK1000F", credits=15)))
    (slot,) = [r for r in rows.plan_reasons if r.details]
    assert slot.message == (
        "Add one approved complementary studies course: 2 fit this plan's timetable. 1 of them "
        "are worth fewer than the table's 18 credits, so a plan that takes one is conditional: "
        "confirm it with your advisor."
    )
    assert (slot.kind, slot.details) == (
        "included",
        {
            "credits": 18,
            "fits": ["KKK1001F", "KKK1002F"],
            "untimed": [],
            "fewer_credits": ["KKK1001F"],
            "sections": {},
            "forced": {},
        },
    )


def test_a_slot_records_each_courses_sections_and_what_it_forces(symbols):
    # AAA1000S meets on Monday at 10:00, with lab A on Wednesday and lab B on Friday at 14:00, and
    # either lab fits the plan. AAA1002S meets on Tuesday at 9:00, so the plan itself takes
    # AAA1001S's Thursday tutorial. KKK1000S meets on Wednesday at 14:00, so it forces lab B, while
    # KKK1002S forces nothing. KKK1001S's lecture A clashes on Monday, leaving its lecture B.
    rules = rulebook(
        {
            1: (
                core("y1"),
                CreditsFromGroups(credits=18, from_groups=("complementary",)),
                total(66),
            )
        },
        {
            "y1": ("AAA1000S", "AAA1001S", "AAA1002S"),
            "complementary": ("KKK1000S", "KKK1001S", "KKK1002S"),
        },
        [course(c) for c in ("AAA1000S", "AAA1001S", "AAA1002S")]
        + [course(c, 18) for c in ("KKK1000S", "KKK1001S", "KKK1002S")],
        [
            meeting("AAA1000S", 1, 10),
            meeting("AAA1000S", 3, 14, ("lab", "A")),
            meeting("AAA1000S", 5, 14, ("lab", "B")),
            meeting("AAA1001S", 2, 9, ("tutorial", "A")),
            meeting("AAA1001S", 4, 9, ("tutorial", "B")),
            meeting("AAA1002S", 2, 9),
            meeting("KKK1000S", 3, 14),
            meeting("KKK1001S", 1, 10, ("lecture", "A")),
            meeting("KKK1001S", 2, 10, ("lecture", "B")),
            meeting("KKK1002S", 4, 11),
        ],
    )
    rows = generate(rules, symbols)
    chosen = {c.course_code: c.choices for c in rows.plan_courses if c.choices}
    assert chosen == {
        "AAA1000S": {"lab": ["A", "B"]},
        "AAA1001S": {"tutorial": ["B"]},
    }
    (slot,) = [r for r in rows.plan_reasons if r.details]
    assert (slot.details["fits"], slot.details["sections"], slot.details["forced"]) == (
        ["KKK1000S", "KKK1001S", "KKK1002S"],
        {"KKK1001S": {"lecture": ["B"]}},
        {"KKK1000S": {"AAA1000S": {"lab": "B"}}},
    )
    # It belongs to the one plan, which is first
    (plan,) = rows.plans
    assert (plan.position, slot.plan_id) == (1, plan.id)


def test_each_reason_cites_the_passage_it_rests_on(symbols):
    # She has her first year's practical training, AAA1000X, signed off, but failed AAA1001S and
    # owes one of its electives. Her second year's core
    # holds AAA2000X, practical training she hasn't finished; AAA2000S, which a person must judge
    # and which has a meeting with no printed time; AAA2001F, which needs a course she hasn't
    # passed; AAA2004F, passed, and AAA2005F, whose supplementary is still to come; AAA2006S, which
    # clashes with AAA1001S; and CSC3024S, whose entry prints its practicals by arrangement
    # (p. 171). AAA2007F, one of its electives, needs a course she hasn't passed. Her third year's
    # AAA3000F needs nothing, and both her years owe 18 complementary credits. Stop 1's decision 20: a table is found by its heading in her curriculum, her year's
    # minimum by its last table, a course by its own entry and a faculty rule by its number.
    complementary = CreditsFromGroups(credits=18, from_groups=("complementary",))
    years = {
        1: (
            core("y1"),
            ChooseFromGroup(choose=1, from_group="g1"),
            complementary,
            total(66),
        ),
        2: (
            core("y2"),
            ChooseFromGroup(choose=1, from_group="g2"),
            complementary,
            total(130),
        ),
        3: (core("y3"), total(16)),
    }
    second = (
        "AAA2000X",
        "AAA2000S",
        "AAA2001F",
        "AAA2004F",
        "AAA2005F",
        "AAA2006S",
        "CSC3024S",
    )
    groups = {
        "y1": ("AAA1000X", "AAA1000F", "AAA1001S"),
        "g1": ("AAA1002F", "AAA1003F"),
        "y2": second,
        "g2": ("AAA2002F", "AAA2003F", "AAA2007F"),
        "y3": ("AAA3000F",),
        "complementary": ("KKK1000F",),
    }
    plain = ("AAA1000F", "AAA1001S", "AAA1002F", "AAA1003F", "AAA2002F", "AAA2003F")
    courses = [
        course(code)
        for code in (*plain, "AAA2004F", "AAA2005F", "AAA2006S", "AAA3000F")
    ]
    courses += [
        course("AAA1000X", 0),
        course("AAA2000X", 0),
        course(
            "AAA2000S", rule=Refer(refer="By permission of the Head of Department.")
        ),
        course("AAA2001F", rule=CourseNeed(course="ZZZ1000F", need="pass")),
        course("AAA2007F", rule=CourseNeed(course="ZZZ1001F", need="pass")),
        course("CSC3024S", 18),
        course("KKK1000F", 18),
    ]
    meetings = [
        meeting("AAA1001S", 1, 14),
        meeting("AAA2006S", 1, 14),
        meeting("AAA2000S", None),
        meeting("KKK1000F", 2, 9),
    ]
    rules = timetabled(rulebook(years, groups, courses, meetings))
    passages = (
        # Another curriculum's table of the same heading, read first
        passage("y2", "EB000BBB01"),
        *(
            passage(table, CURRICULUM, position=n)
            for n, table in enumerate(("y1", "g1", "y2", "g2", "y3"), start=1)
        ),
        *(
            passage(f"{code} entry", course=code)
            for code in (
                "ZZZ1000F",
                "AAA2000X",
                "AAA2000S",
                "AAA2001F",
                "AAA2007F",
                "CSC3024S",
            )
        ),
        passage("FB7"),
        passage("FB3.4"),
    )
    rules = rules.model_copy(update={"passages": passages})
    history = (
        line("AAA1000X", credits=0),
        line("AAA1000F"),
        line("AAA1001S", "F"),
        line("AAA2004F"),
        line("AAA2005F", "FS"),
    )
    rows = generate(rules, symbols, history, intake=2024)
    assert len(rows.plans) == 4  # one elective from each year's group
    assert cited(rules, rows) == Counter(
        {
            # Her year's core, her first year's, and each year rule she owes
            (True, "included", None, (CURRICULUM, "y2")): 1,
            (True, "included", None, (CURRICULUM, "y1")): 1,
            (True, "included", None, (CURRICULUM, "g1")): 1,
            # g2's rule, and her year's minimum, as g2 is its last table
            (True, "included", None, (CURRICULUM, "g2")): 2,
            (True, "included", None, (CURRICULUM, "y3")): 1,
            (True, "excluded", None, (CURRICULUM, "g2")): 1,
            (True, "conditional", "AAA2000X", (None, "AAA2000X entry")): 1,
            (True, "conditional", "AAA2005F", (None, "FB7")): 1,
            (True, "conflict", "AAA2006S", (None, "FB3.4")): 1,
            (True, "excluded", "AAA2001F", (None, "AAA2001F entry")): 1,
            (True, "excluded", "AAA2007F", (None, "AAA2007F entry")): 1,
            (True, "conditional", "AAA2000S", (None, "AAA2000S entry")): 1,
            (True, "conditional", "AAA2000S", (None, "FB3.4")): 1,
            (True, "conditional", "CSC3024S", (None, "CSC3024S entry")): 1,
            # Each plan's two complementary lines, by the table of each line's year
            (False, "included", None, (CURRICULUM, "y1")): 4,
            (False, "included", None, (CURRICULUM, "y2")): 4,
        }
    )
    said = messages(rows, "included")
    # Her year's minimum: its 130, less AAA2004F's and AAA2005F's 32 and the 32 of AAA2001F and
    # AAA2006S, which aren't in her plans
    for words in (
        "Every plan holds the core courses you still need this year: AAA2000S and CSC3024S.",
        "Every plan holds AAA1001S, which you still owe from your first year.",
        "Every plan takes at least 1 of AAA1002F and AAA1003F to finish your first year.",
        (
            "Every plan comes to at least 66 credits for the year, counting its complementary "
            "studies."
        ),
    ):
        assert words in said
    # An elective she can't take yet is in no plan, and leaves her advisor nothing to settle
    assert (
        "AAA2007F isn't in any plan, as it needs ZZZ1001F, which your record doesn't show yet."
    ) in messages(rows, "excluded")


@pytest.mark.parametrize(
    ("passed", "fits"),
    [
        # Neither passed, so the place lists the 8-credit course and not the 7-credit one
        ((), [["KKK1000F"]]),
        # The 8-credit one fills it
        (("KKK1000F",), []),
        # The 7-credit one doesn't, so the place still lists the other
        (("KKK1001F",), [["KKK1000F"]]),
    ],
)
def test_a_576_credit_place_takes_a_complementary_course_of_at_least_8_credits(
    passed, fits, symbols
):
    # EB011's footnotes place ASL1200S and CON2026S in its second year, and she has passed
    # CON2026S
    credits = {"KKK1000F": 8, "KKK1001F": 7}
    history = (
        line("AAA1000F"),
        line("CON2026S", credits=8),
        *(line(code, credits=credits[code]) for code in passed),
    )
    rules = eb011(tuple(credits.items()))
    rows = generate(rules, symbols, history, 2024, "EB011EEE05")
    assert [r.details["fits"] for r in rows.plan_reasons if r.details] == fits


def eb011(complementary: tuple[tuple[str, int], ...] = (("KKK1000F", 15),)) -> RuleSet:
    # Three made-up years under EB011's code, so its 2026 footnotes apply and her second year isn't
    # her last, with these approved complementary courses and their credits
    return rulebook(
        {number: (core(f"y{number}"), total(16)) for number in (1, 2, 3)},
        {
            "y1": ("AAA1000F",),
            "y2": ("AAA2000F",),
            "y3": ("AAA3000F",),
            "complementary": tuple(code for code, _ in complementary),
        },
        [course(f"AAA{n}000F") for n in (1, 2, 3)]
        + [course(code, credits) for code, credits in complementary],
        curriculum="EB011EEE05",
    )


@pytest.mark.parametrize(
    ("intake", "passed", "places"),
    [
        (2024, "CON2026S", ["ASL1200S"]),
        (2024, "ASL1200S", ["CON2026S"]),
        (2025, "CON2026S", []),
    ],
)
def test_a_576_credit_student_gets_a_place_for_each_course_she_still_owes(
    intake, passed, places, symbols
):
    # EB011's footnotes place ASL1200S and CON2026S in its second year, and she has passed one of
    # them. A place takes an approved complementary course of at least 8 credits.
    history = (line("AAA1000F"), line(passed, credits=8))
    tables = {
        "ASL1200S": "First Year Core Courses (ME)",
        "CON2026S": "Second Year Core Courses (ME)",
    }
    rules = eb011().model_copy(
        update={
            "passages": tuple(
                passage(table, "EB011EEE05", position=n)
                for n, table in enumerate(tables.values())
            )
        }
    )
    rows = generate(rules, symbols, history, intake, "EB011EEE05")
    assert plans(rows) == [("AAA2000F",)]
    owed = [r for r in rows.plan_reasons if r.details]
    assert [r.details["owed"] for r in owed] == places
    assert all(r.details["credits"] == 8 for r in owed)
    sections = {p.id: p.section for p in rules.passages}
    assert [sections[r.passage_id] for r in owed] == [tables[code] for code in places]
    assert [r.message for r in owed] == [
        f"Your 576-credit curriculum still needs {code}. Take an approved complementary "
        "studies course of at least 8 credits in its place: 1 fit this plan's timetable."
        for code in places
    ]


def test_a_pass_in_one_offering_counts_once_towards_complementary_credits_and_places(
    symbols,
):
    # Her KKK1000F covers KKK1000S, its other offering at the same credits, but it's one pass: it
    # meets her second year's 18 complementary credits, so the ASL1200S place EB011's footnote puts
    # in that year is still hers to fill
    rules = rulebook(
        {
            1: (core("y1"), total(16)),
            2: (
                core("y2"),
                CreditsFromGroups(credits=18, from_groups=("complementary",)),
                total(34),
            ),
            3: (core("y3"), total(16)),
        },
        {
            "y1": ("AAA1000F",),
            "y2": ("AAA2000F",),
            "y3": ("AAA3000F",),
            "complementary": ("KKK1000F", "KKK1000S"),
        },
        [course(f"AAA{n}000F") for n in (1, 2, 3)]
        + [course("KKK1000F", 18), course("KKK1000S", 18)],
        curriculum="EB011EEE05",
    )
    history = (
        line("AAA1000F"),
        line("CON2026S", credits=8),
        line("KKK1000F", credits=18),
    )
    rows = generate(rules, symbols, history, 2024, "EB011EEE05")
    assert [r.details.get("owed") for r in rows.plan_reasons if r.details] == [
        "ASL1200S"
    ]


def test_a_passed_complementary_course_fills_a_576_credit_place(symbols):
    # KKK1000F is left over once her complementary credits, of which she owes none, are met, so it
    # stands in for ASL1200S
    history = (
        line("AAA1000F"),
        line("CON2026S", credits=8),
        line("KKK1000F", credits=15),
    )
    rows = generate(eb011(), symbols, history, 2024, "EB011EEE05")
    assert plans(rows) == [("AAA2000F",)]
    assert [r.details for r in rows.plan_reasons if r.details] == []


def test_fewer_conditional_courses_then_fewer_credits_rank_first(symbols):
    # AAA1001F's printed requirement needs a person, and AAA1003F is 18 credits
    rules = rulebook(
        {1: (core("y1"), ChooseFromGroup(choose=1, from_group="g"), total(32))},
        {"y1": ("AAA1000F",), "g": ("AAA1001F", "AAA1002F", "AAA1003F")},
        [
            course("AAA1000F"),
            course("AAA1001F", rule=Refer(refer="By permission of the convener.")),
            course("AAA1002F"),
            course("AAA1003F", 18),
        ],
    )
    assert plans(generate(rules, symbols)) == [
        ("AAA1000F", "AAA1002F"),
        ("AAA1000F", "AAA1003F"),
        ("AAA1000F", "AAA1001F"),
    ]


@pytest.mark.parametrize(
    ("count", "logged"), [(50, []), (51, ["Kept the best 50 of 51 plans"])]
)
def test_a_set_keeps_its_best_50_plans_and_logs_any_it_cuts(
    count, logged, symbols, caplog
):
    # One elective of this many makes one plan each
    codes = [f"AAA{1001 + n}F" for n in range(count)]
    rules = rulebook(
        {1: (core("y1"), ChooseFromGroup(choose=1, from_group="g"), total(32))},
        {"y1": ("AAA1000F",), "g": tuple(codes)},
        [course("AAA1000F")] + [course(code) for code in codes],
    )
    with caplog.at_level("WARNING", logger="sage.engine.generator"):
        rows = generate(rules, symbols)
    assert len(rows.plans) == 50
    assert caplog.messages == logged


@pytest.mark.parametrize(
    ("electives", "named", "combined"),
    [
        ((), "Core Courses Only", None),
        (("EEE4119F",), "Robotics", "EEE4119F"),
        (("EEE4117F", "HUB4049F"), "Power & Imaging", "EEE4117F · HUB4049F"),
        (
            ("EEE4117F", "EEE4118F", "EEE4119F"),
            "Power, Control & Robotics",
            "EEE4117F · EEE4118F · EEE4119F",
        ),
        # Networks, Control and Control: the shared word comes once, where its first elective
        # puts it, so not in alphabetical order
        (
            ("CSC3002F", "EEE3094S", "EEE4118F"),
            "Networks & Control",
            "CSC3002F · EEE3094S · EEE4118F",
        ),
    ],
)
def test_a_plan_is_named_by_its_electives_theme_words(electives, named, combined):
    # My words for its electives in code order, written "A, B & C", over their codes as the
    # prototype prints them, and "Core Courses Only" when it has none
    assert (name(electives, {}), combination(electives)) == (named, combined)


def test_a_plan_is_stored_with_its_name_and_combination(symbols):
    # AAA1001F has no theme word, so its printed name names its plan
    rules = rulebook(
        {1: (core("y1"), ChooseFromGroup(choose=1, from_group="g"), total(32))},
        {"y1": ("AAA1000F",), "g": ("AAA1001F", "EEE4119F")},
        [course(code) for code in ("AAA1000F", "AAA1001F", "EEE4119F")],
    )
    rows = generate(rules, symbols)
    assert {(plan.name, plan.combination) for plan in rows.plans} == {
        ("Course AAA1001F", "AAA1001F"),
        ("Robotics", "EEE4119F"),
    }


def test_the_same_record_gets_the_same_ids(symbols):
    rules = rulebook(
        {1: (core("y1"), ChooseFromGroup(choose=1, from_group="g"), total(32))},
        {"y1": ("AAA1000F",), "g": ("AAA1001F", "AAA1002F")},
        [course(code) for code in ("AAA1000F", "AAA1001F", "AAA1002F")],
    )
    first, second = generate(rules, symbols), generate(rules, symbols)
    assert first.plan_set.id == second.plan_set.id
    assert [p.id for p in first.plans] == [p.id for p in second.plans]
    assert [r.id for r in first.plan_reasons] == [r.id for r in second.plan_reasons]


@pytest.mark.parametrize(
    ("passed", "intake", "electives"), [(512, 2025, 2), (511, 2025, 3), (512, 2024, 2)]
)
def test_a_final_year_reaches_the_degree_total(passed, intake, electives, symbols):
    # EB009's first page prints 560 credits for a 2025 intake. With 512 passed her last year needs
    # 48, which the core and two electives make; with 511 it needs 49, so three. It prints 576
    # before, so a 2024 intake with 512 passed needs 64, of which her two 576-credit places, which
    # EB009's footnotes put in its first year, take 16, and the core and two electives the rest.
    rules = rulebook(
        {
            1: (core("y1"), total(512)),
            2: (
                core("y2"),
                CreditsFromGroups(credits=16, from_groups=("g",)),
                total(32),
            ),
        },
        {
            "y1": ("AAA1000F",),
            "y2": ("AAA2000S",),
            "g": ("AAA2001S", "AAA2002S", "AAA2003S"),
        },
        [course("AAA1000F", passed)]
        + [course(code) for code in ("AAA2000S", "AAA2001S", "AAA2002S", "AAA2003S")],
        curriculum="EB009EEE01",
    )
    history = (line("AAA1000F", credits=passed),)
    rows = generate(rules, symbols, history, intake, "EB009EEE01")
    assert {len(courses) - 1 for courses in plans(rows)} == {electives}


@pytest.mark.parametrize(
    ("passed", "advice"),
    [
        (512, "See your advisor about it."),
        (
            513,
            (
                "Your year is now under its printed minimum of 48 credits, and your advisor "
                "can give permission for that."
            ),
        ),
    ],
)
def test_a_left_out_course_puts_her_year_under_its_minimum_unless_the_degree_needs_it(
    passed, advice, symbols
):
    # EB009's first page prints 560 credits for a 2025 intake. Her last year's 48 counts AAA2002S,
    # which she has passed, and KKK1000F, which meets its 18 complementary credits, and AAA2001S
    # needs ZZZ1000F, which she hasn't passed. With 512 credits of her first year as well, the
    # degree still needs 14 from her plans, which with those two's 34 make the year's 48, and with
    # 513 only 13, under it. Both take the same plans.
    rules = rulebook(
        {
            1: (core("y1"), total(passed)),
            2: (
                core("y2"),
                CreditsFromGroups(credits=16, from_groups=("g",)),
                CreditsFromGroups(credits=18, from_groups=("complementary",)),
                total(48),
            ),
        },
        {
            "y1": ("AAA1000F",),
            "y2": ("AAA2000S", "AAA2001S", "AAA2002S"),
            "g": ("AAA2003S", "AAA2004S"),
            "complementary": ("KKK1000F",),
        },
        [
            course("AAA1000F", passed),
            course("AAA2000S"),
            course("AAA2001S", rule=CourseNeed(course="ZZZ1000F", need="pass")),
            course("AAA2002S"),
            course("AAA2003S"),
            course("AAA2004S"),
            course("KKK1000F", 18),
        ],
        curriculum="EB009EEE01",
    )
    history = (
        line("AAA1000F", credits=passed),
        line("AAA2002S"),
        line("KKK1000F", credits=18),
    )
    rows = generate(rules, symbols, history, curriculum="EB009EEE01")
    assert sorted(plans(rows)) == [("AAA2000S", "AAA2003S"), ("AAA2000S", "AAA2004S")]
    assert messages(rows, "excluded")[-1] == (
        "AAA2001S isn't in your plans, as it needs ZZZ1000F, which your record doesn't show "
        f"yet. {advice}"
    )


@pytest.mark.parametrize(
    ("passed", "early"),
    [
        (
            ("ZZZ1000F", "AAA2003F"),
            [
                (
                    "Next year's core includes AAA2000F, whose entry rules you already meet. "
                    "Students sometimes take such courses early, with their advisor's "
                    "agreement."
                )
            ],
        ),
        (("AAA2003F",), []),
    ],
)
def test_next_years_core_she_already_meets_the_rules_for_is_named(
    passed, early, symbols
):
    # Her second year's core: AAA2000F needs ZZZ1000F, AAA2001F needs ZZZ1001F, which she hasn't
    # passed, AAA2002F needs a person's judgement, and she has passed AAA2003F early, which keeps
    # her in her first year. Only AAA2000F can be named, and only once she has ZZZ1000F.
    rules = rulebook(
        {1: (core("y1"), total(32)), 2: (core("y2"), total(64))},
        {
            "y1": ("AAA1000F", "AAA1001F"),
            "y2": ("AAA2000F", "AAA2001F", "AAA2002F", "AAA2003F"),
        },
        [
            course("AAA1000F"),
            course("AAA1001F"),
            course("AAA2000F", rule=CourseNeed(course="ZZZ1000F", need="pass")),
            course("AAA2001F", rule=CourseNeed(course="ZZZ1001F", need="pass")),
            course(
                "AAA2002F", rule=Refer(refer="By permission of the Head of Department.")
            ),
            course("AAA2003F"),
        ],
    )
    rows = generate(rules, symbols, tuple(line(code) for code in passed))
    assert plans(rows) == [("AAA1000F", "AAA1001F")]
    named = [m for m in messages(rows, "included") if m.startswith("Next year's core")]
    assert named == early


def test_a_core_result_still_to_come_counts_as_passed_with_its_reason(symbols):
    # Her AAA1001F result isn't out, so her plans are for her second year
    rules = rulebook(
        {1: (core("y1"), total(32)), 2: (core("y2"), total(16))},
        {"y1": ("AAA1000F", "AAA1001F"), "y2": ("AAA2000F",)},
        [course(code) for code in ("AAA1000F", "AAA1001F", "AAA2000F")],
    ).model_copy(update={"passages": (passage("AAA1001F entry", course="AAA1001F"),)})
    rows = generate(rules, symbols, (line("AAA1000F"), line("AAA1001F", "OS")))
    assert plans(rows) == [("AAA2000F",)]
    assert (
        "Your result for AAA1001F isn't out yet. These plans assume you pass it, so see your "
        "advisor if you don't."
    ) in messages(rows, "conditional")
    assert (
        cited(rules, rows)[(True, "conditional", "AAA1001F", (None, "AAA1001F entry"))]
        == 1
    )


def test_a_2023_year_has_no_timetable_or_complementary_list_to_check(symbols):
    # 2023 prints no timetable and no approved complementary list (14 Oct), so its plans can't be
    # checked for clashes, and a complementary line lists nothing (Stop 1's decision 16)
    rules = rulebook(
        {
            1: (
                core("y1"),
                CreditsFromGroups(credits=18, from_groups=("complementary",)),
                total(34),
            )
        },
        {"y1": ("AAA1000F",), "complementary": ()},
        [course("AAA1000F")],
    ).model_copy(
        update={
            "handbook_versions": (HandbookVersion(year=2023, approved=True),),
            "passages": (passage("FB3.4"),),
        }
    )
    rows = generate(rules, symbols)
    assert plans(rows) == [("AAA1000F",)]
    assert cited(rules, rows)[(True, "conditional", None, (None, "FB3.4"))] == 1
    assert messages(rows, "conditional") == [
        (
            "This year's rules have no timetable, so SAGE couldn't check these plans for clashes. "
            "Check them with your advisor."
        ),
        (
            "Add one approved complementary studies course, though none on the approved list fits "
            "this plan's timetable, so see your advisor."
        ),
    ]


def test_a_year_with_no_course_she_can_take_yet_says_so(symbols):
    # Her year's only core course needs ZZZ1000F, which she hasn't passed
    rules = rulebook(
        {1: (core("y1"), total(16))},
        {"y1": ("AAA1000F",)},
        [course("AAA1000F", rule=CourseNeed(course="ZZZ1000F", need="pass"))],
    )
    rows = generate(rules, symbols)
    assert rows.plans == ()
    assert messages(rows, "conflict") == [
        (
            "None of the courses your year still needs can be taken yet, so there's no plan to "
            "list. See your advisor."
        )
    ]


def beyond(curriculum: str, number: int) -> RuleSet:
    # A made-up curriculum a year longer than the given year, with one core course a year, so the
    # degree's total never applies to that year
    years = range(1, number + 2)
    return rulebook(
        {year: (core(f"y{year}"), total(16)) for year in years},
        {f"y{year}": (f"AAA{year}000F",) for year in years},
        [course(f"AAA{year}000F") for year in years],
        curriculum=curriculum,
    )


@pytest.mark.parametrize(
    ("curriculum", "noted"), [("EB009EEE01", True), ("EB011EEE05", False)]
)
def test_eb009s_final_year_carries_its_note_on_shared_slots(curriculum, noted, symbols):
    # pp. 49 and 51 print the note under EB009's and EB809's final-year electives, and EB011's
    # final year prints none
    history = tuple(line(f"AAA{year}000F") for year in (1, 2, 3))
    table = "Fourth Year Elective Core Courses (EE)"
    rules = beyond(curriculum, 4).model_copy(
        update={"passages": (passage(table, curriculum),)}
    )
    rows = generate(rules, symbols, history, curriculum=curriculum)
    assert plans(rows) == [("AAA4000F",)]
    quoted = (
        'The handbook notes, without naming them: "Some elective core courses in the first '
        'semester are in the same timetable slots and cannot be taken concurrently." Check '
        "your electives with your advisor."
    )
    assert (quoted in messages(rows, "conditional")) is noted
    assert cited(rules, rows)[(True, "conditional", None, (curriculum, table))] == noted


def test_a_student_with_every_years_core_done_gets_no_plans_and_says_why(symbols):
    # Each of the three years holds one core course, and she has passed them all
    history = tuple(line(f"AAA{year}000F") for year in (1, 2, 3))
    rows = generate(beyond(CURRICULUM, 2), symbols, history)
    assert rows.plans == ()
    assert messages(rows, "conflict") == [
        (
            "Your record shows every year's core courses done, so there's no year left to plan. "
            "See your advisor."
        )
    ]


def test_an_eb022_set_quotes_note_i_on_taking_all_three(symbols):
    # p. 53's note (i) under EB022's third-year elective core courses
    rules = rulebook(
        {
            1: (core("y1"), total(16)),
            2: (core("y2"), total(16)),
            3: (core("y3"), ChooseFromGroup(choose=2, from_group="g"), total(48)),
            4: (core("y4"), total(16)),
        },
        {
            "y1": ("AAA1000F",),
            "y2": ("AAA2000F",),
            "y3": ("AAA3000F",),
            "y4": ("AAA4000F",),
            "g": ("AAA3001S", "AAA3002S", "AAA3003S"),
        },
        [
            course(code)
            for code in (
                "AAA1000F",
                "AAA2000F",
                "AAA3000F",
                "AAA3001S",
                "AAA3002S",
                "AAA3003S",
                "AAA4000F",
            )
        ],
        curriculum="EB022EEE02",
    )
    history = (line("AAA1000F"), line("AAA2000F"))
    (more,) = messages(
        generate(rules, symbols, history, curriculum="EB022EEE02"), "excluded"
    )
    assert more.endswith(
        "but then the complementary studies elective should then be taken in the winter or "
        'summer term."'
    )


def test_mbalis_plans_are_her_seeds_10(approved_2026, seed_file, symbols):
    # Her seed's plans were written by hand from print: the core, two or three of EEE4117F,
    # EEE4118F and EEE4119F, and one of EEE4114F, EEE4120F and HUB4049F when only two
    seeded = load_seed(seed_file, STUDENT)
    rows = ClingoPlanGenerator().generate(
        seeded.student, seeded.course_history, approved_2026, symbols
    )
    expected = {
        frozenset(c.course_code for c in seeded.plan_courses if c.plan_id == plan.id)
        for plan in seeded.plans
    }
    assert {frozenset(courses) for courses in plans(rows)} == expected
    assert len(rows.plans) == 10
