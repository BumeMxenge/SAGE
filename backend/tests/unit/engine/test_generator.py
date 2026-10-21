# Checks the plan sets the generator builds, on small years made up for each test with every plan
# and reason worked out by hand, and on Mbali's own record against the approved 2026, whose plans
# must be her seed's 10, written by hand from print
from datetime import time
from uuid import UUID, uuid4

import pytest

from sage.engine.generator import ClingoPlanGenerator
from sage.shared.rules import (
    TERM_BY_SUFFIX,
    AllOfGroup,
    ChooseFromGroup,
    Course,
    CourseGroup,
    CourseGroupMember,
    CourseNeed,
    CreditsFromGroups,
    CurriculumRule,
    HandbookVersion,
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


def test_a_course_she_has_passed_in_a_group_counts_towards_its_rule(symbols):
    # She took AAA1001F early, so choosing 2 of the three leaves 1 more, and her year's 48 drops by
    # its 16 to 32, which the core and one more make
    rules = rulebook(
        {1: (core("y1"), ChooseFromGroup(choose=2, from_group="g"), total(48))},
        {"y1": ("AAA1000F",), "g": ("AAA1001F", "AAA1002F", "AAA1003F")},
        [course(code) for code in ("AAA1000F", "AAA1001F", "AAA1002F", "AAA1003F")],
    )
    rows = generate(rules, symbols, (line("AAA1001F"),))
    assert sorted(plans(rows)) == [("AAA1000F", "AAA1002F"), ("AAA1000F", "AAA1003F")]


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


def test_two_current_core_courses_that_clash_leave_no_plan_and_say_why(symbols):
    rules = rulebook(
        {1: (core("y1"), total(32))},
        {"y1": ("AAA1000F", "AAA1001F")},
        [course("AAA1000F"), course("AAA1001F")],
        [meeting("AAA1000F", 1, 10), meeting("AAA1001F", 1, 10)],
    )
    rows = generate(rules, symbols)
    assert rows.plans == ()
    assert messages(rows, "conflict") == [
        "No plan can hold AAA1000F and AAA1001F together, so see your advisor."
    ]


def test_a_core_course_she_cant_take_yet_is_left_out_and_her_minimum_drops(symbols):
    # AAA1001F needs ZZZ1000F, which she hasn't passed. Without it her year's 48 drops by its 16 to
    # 32, which one elective beside AAA1000F makes; had it not dropped, she'd need both.
    rules = rulebook(
        {
            1: (
                core("y1"),
                CreditsFromGroups(credits=16, from_groups=("g",)),
                total(48),
            )
        },
        {"y1": ("AAA1000F", "AAA1001F"), "g": ("AAA1002F", "AAA1003F")},
        [
            course("AAA1000F"),
            course("AAA1001F", rule=CourseNeed(course="ZZZ1000F", need="pass")),
            course("AAA1002F"),
            course("AAA1003F"),
        ],
    )
    rows = generate(rules, symbols)
    assert sorted(plans(rows)) == [("AAA1000F", "AAA1002F"), ("AAA1000F", "AAA1003F")]
    assert messages(rows, "excluded")[-1] == (
        "AAA1001F isn't in your plans, as it needs ZZZ1000F, which your record doesn't show "
        "yet. Your year is now under its printed minimum of 48 credits, and your advisor can "
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
    # and KKK1002F meets on Tuesday.
    rules = rulebook(
        {
            1: (
                core("y1"),
                CreditsFromGroups(credits=18, from_groups=("complementary",)),
                total(34),
            )
        },
        {"y1": ("AAA1000F",), "complementary": ("KKK1000F", "KKK1001F", "KKK1002F")},
        [course("AAA1000F")]
        + [course(c, 18) for c in ("KKK1000F", "KKK1001F", "KKK1002F")],
        [
            meeting("AAA1000F", 1, 10),
            meeting("KKK1000F", 1, 10),
            meeting("KKK1001F", None),
            meeting("KKK1002F", 2, 10),
        ],
    )
    rows = generate(rules, symbols)
    (slot,) = [r for r in rows.plan_reasons if r.details]
    assert (slot.kind, slot.course_code, slot.details) == (
        "included",
        None,
        {
            "credits": 18,
            "fits": ["KKK1001F", "KKK1002F"],
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
    assert chosen == {"AAA1001S": {"tutorial": "B"}}
    (slot,) = [r for r in rows.plan_reasons if r.details]
    assert (slot.details["fits"], slot.details["sections"], slot.details["forced"]) == (
        ["KKK1000S", "KKK1001S", "KKK1002S"],
        {"KKK1001S": {"lecture": ["B"]}},
        {"KKK1000S": {"AAA1000S": {"lab": "B"}}},
    )


def eb011() -> RuleSet:
    # Three made-up years under EB011's code, so its 2026 footnotes apply and her second year isn't
    # her last
    return rulebook(
        {number: (core(f"y{number}"), total(16)) for number in (1, 2, 3)},
        {
            "y1": ("AAA1000F",),
            "y2": ("AAA2000F",),
            "y3": ("AAA3000F",),
            "complementary": ("KKK1000F",),
        },
        [course(f"AAA{n}000F") for n in (1, 2, 3)] + [course("KKK1000F", 15)],
        curriculum="EB011EEE05",
    )


@pytest.mark.parametrize(("intake", "places"), [(2024, ["ASL1200S"]), (2025, [])])
def test_a_576_credit_student_owing_asl1200s_gets_a_place(intake, places, symbols):
    # EB011's footnotes place ASL1200S and CON2026S in its second year, and she has passed
    # CON2026S. A place takes an approved complementary course of at least 8 credits.
    history = (line("AAA1000F"), line("CON2026S", credits=8))
    rows = generate(eb011(), symbols, history, intake, "EB011EEE05")
    assert plans(rows) == [("AAA2000F",)]
    owed = [r.details for r in rows.plan_reasons if r.details]
    assert [d["owed"] for d in owed] == places
    assert all(d["credits"] == 8 for d in owed)


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


def test_51_plans_keep_the_best_50_and_say_so_in_the_log(symbols, caplog):
    codes = [f"AAA{1001 + n}F" for n in range(51)]
    rules = rulebook(
        {1: (core("y1"), ChooseFromGroup(choose=1, from_group="g"), total(32))},
        {"y1": ("AAA1000F",), "g": tuple(codes)},
        [course("AAA1000F")] + [course(code) for code in codes],
    )
    with caplog.at_level("WARNING", logger="sage.engine.generator"):
        rows = generate(rules, symbols)
    assert len(rows.plans) == 50
    assert caplog.messages == ["Kept the best 50 of 51 plans"]


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


@pytest.mark.parametrize(("passed", "electives"), [(512, 2), (511, 3)])
def test_a_final_year_reaches_the_degree_total(passed, electives, symbols):
    # EB009's first page prints 560 credits for a 2025 intake. With 512 passed her last year needs
    # 48, which the core and two electives make; with 511 it needs 49, so three.
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
    rows = generate(rules, symbols, history, curriculum="EB009EEE01")
    assert {len(courses) - 1 for courses in plans(rows)} == {electives}


def test_a_core_result_still_to_come_counts_as_passed_with_its_reason(symbols):
    # Her AAA1001F result isn't out, so her plans are for her second year
    rules = rulebook(
        {1: (core("y1"), total(32)), 2: (core("y2"), total(16))},
        {"y1": ("AAA1000F", "AAA1001F"), "y2": ("AAA2000F",)},
        [course(code) for code in ("AAA1000F", "AAA1001F", "AAA2000F")],
    )
    rows = generate(rules, symbols, (line("AAA1000F"), line("AAA1001F", "OS")))
    assert plans(rows) == [("AAA2000F",)]
    assert (
        "Your result for AAA1001F isn't out yet. These plans assume you pass it, so see your "
        "advisor if you don't."
    ) in messages(rows, "conditional")


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
    rows = generate(beyond(curriculum, 4), symbols, history, curriculum=curriculum)
    assert plans(rows) == [("AAA4000F",)]
    quoted = (
        'The handbook notes, without naming them: "Some elective core courses in the first '
        'semester are in the same timetable slots and cannot be taken concurrently." Check '
        "your electives with your advisor."
    )
    assert (quoted in messages(rows, "conditional")) is noted


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
