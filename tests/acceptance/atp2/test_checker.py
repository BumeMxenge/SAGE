# Checks ATP-2's checker on small made-up years, each worked out by hand from SEMANTICS.md, with
# boundaries on both sides. They're its gate: make atp2 runs no record until they pass.
import json
from collections.abc import Sequence
from datetime import time
from itertools import count
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from checker.plans import Slot, check, year_of_study
from checker.record import Covers
from checker.week import Meeting, Week, schedulable

from sage.shared.rules import (
    COMPLEMENTARY,
    TERM_BY_SUFFIX,
    Course,
    CourseGroup,
    CourseGroupMember,
    Curriculum,
    CurriculumRule,
    Equivalence,
    HandbookVersion,
    ResultSymbol,
    RuleSet,
    TimetableSlot,
)
from sage.shared.students import CourseHistoryLine, Student

SYMBOLS_FILE = (
    Path(__file__).resolve().parents[3] / "backend/tests/fixtures/result_symbols.json"
)
SYMBOLS = {
    row["symbol"]: ResultSymbol(**row)
    for row in json.loads(SYMBOLS_FILE.read_text(encoding="utf-8"))
}
CURRICULUM = "XX001ABC01"
SHE = Student(id=UUID(int=1), curriculum_code=CURRICULUM, intake_year=2026)
SLOT_IDS = count(1)


def course(code: str, credits: int = 16, rule: dict[str, Any] | None = None) -> Course:
    return Course(
        handbook_year=2026,
        code=code,
        name=code,
        credits=credits,
        nqf_level=5,
        term=TERM_BY_SUFFIX[code[-1]],
        entry_rule=rule,
    )


def meets(
    code: str, day: int, start: str, end: str, choice: str | None = None
) -> TimetableSlot:
    # A lecture in its course's term, as one of the group's sections when it has a choice
    return TimetableSlot(
        id=UUID(int=next(SLOT_IDS)),
        handbook_year=2026,
        course_code=code,
        term=TERM_BY_SUFFIX[code[-1]],
        day=day,
        start_time=time.fromisoformat(start),
        end_time=time.fromisoformat(end),
        kind="lecture",
        choice_group="lecture" if choice else None,
        choice=choice,
    )


def line(
    code: str, result: str, mark: int | None, credits: int = 16
) -> CourseHistoryLine:
    return CourseHistoryLine(
        student_id=SHE.id,
        academic_year=2025,
        term=TERM_BY_SUFFIX[code[-1]],
        course_code=code,
        course_name=code,
        credits=credits,
        nqf_level=5,
        result=result,
        mark=mark,
    )


# Year 2's one course, so that year 1 is never her final year
LATER = course("ZZZ2001F")


def her_year(
    core: Sequence[Course],
    *,
    total: int,
    electives: Sequence[Course] = (),
    lines: Sequence[int] = (),
    complementary: Sequence[Course] = (),
    extra: Sequence[Course] = (),
    meetings: Sequence[TimetableSlot] = (),
    equivalences: Sequence[tuple[str, str]] = (),
) -> RuleSet:
    # A made-up curriculum whose first year is hers: its core, choose 1 from its electives, a
    # complementary line of each credits given, and its printed total
    rules: list[dict[str, Any]] = [
        {"all_of_group": "y1-core"},
        {"total_credits": total},
    ]
    groups = {"y1-core": core, "y2-core": [LATER], COMPLEMENTARY: complementary}
    if electives:
        rules.append({"choose": 1, "from_group": "y1-electives"})
        groups["y1-electives"] = electives
    rules += [{"credits": c, "from_groups": [COMPLEMENTARY]} for c in lines]
    later = {"all": [{"all_of_group": "y2-core"}, {"total_credits": 16}]}
    held = {c.code: c for c in (*core, *electives, *complementary, *extra, LATER)}
    return RuleSet(
        handbook_versions=(HandbookVersion(year=2026, approved=True),),
        curricula=(
            Curriculum(
                handbook_year=2026,
                code=CURRICULUM,
                name="Made-up",
                department="Made-up",
            ),
        ),
        curriculum_rules=tuple(
            CurriculumRule(
                handbook_year=2026,
                curriculum_code=CURRICULUM,
                year_of_study=year,
                rule=rule,
            )
            for year, rule in ((1, {"all": rules}), (2, later))
        ),
        courses=tuple(held.values()),
        course_groups=tuple(
            CourseGroup(handbook_year=2026, group_key=key, label=key) for key in groups
        ),
        course_group_members=tuple(
            CourseGroupMember(handbook_year=2026, group_key=key, course_code=c.code)
            for key, members in groups.items()
            for c in members
        ),
        equivalences=tuple(
            Equivalence(handbook_year=2026, course_code=code, counts_as=other)
            for code, other in equivalences
        ),
        timetable_slots=tuple(meetings),
    )


def plans(rules: RuleSet, history: Sequence[CourseHistoryLine] = ()) -> list[set[str]]:
    return [set(plan) for plan in check(SHE, history, rules, SYMBOLS).plans]


@pytest.mark.parametrize(
    ("start", "expected"),
    [
        # BBB1002F starts as AAA1001F ends, at 10:00, so they only touch: one plan holds both
        ("10:00", [{"AAA1001F", "BBB1002F"}]),
        # A minute earlier they overlap, and two current-year core courses that clash leave no plan
        ("09:59", []),
    ],
)
def test_meetings_that_only_touch_dont_clash(
    start: str, expected: list[set[str]]
) -> None:
    rules = her_year(
        [course("AAA1001F"), course("BBB1002F")],
        total=32,
        meetings=[
            meets("AAA1001F", 1, "09:00", "10:00"),
            meets("BBB1002F", 1, start, "11:00"),
        ],
    )
    assert plans(rules) == expected


@pytest.mark.parametrize(
    ("mark", "status"),
    [
        (45, "eligible"),  # exactly min_mark meets a mark leaf, pass or not
        (44, "not_eligible"),
    ],
)
def test_a_mark_at_min_mark_meets_its_leaf(mark: int, status: str) -> None:
    rule = {"course": "BBB2001F", "need": "mark", "min_mark": 45}
    rules = her_year(
        [course("AAA1001F")], total=16, extra=[course("BBB2002S", rule=rule)]
    )
    checked = check(SHE, [line("BBB2001F", "F", mark)], rules, SYMBOLS)
    assert checked.statuses["BBB2002S"] == status


@pytest.mark.parametrize(
    ("min_mark", "status"),
    [
        (50, "check"),  # a supplementary still to come may yet reach 50
        (51, "not_eligible"),  # FB7.3 caps it at 50, so anything above is out of reach
    ],
)
def test_a_pending_supplementary_reaches_50_at_most(min_mark: int, status: str) -> None:
    rule = {"course": "BBB2001F", "need": "mark", "min_mark": min_mark}
    rules = her_year(
        [course("AAA1001F")], total=16, extra=[course("BBB2002S", rule=rule)]
    )
    checked = check(SHE, [line("BBB2001F", "FS", 46)], rules, SYMBOLS)
    assert checked.statuses["BBB2002S"] == status


@pytest.mark.parametrize(
    ("code", "credits", "target", "covered"),
    [
        # PHY1013F's other offering, PHY1013S, which the rules hold at 18 credits, then that
        # offering's equivalence: one step of each
        ("PHY1013F", 18, "PHY1015S", True),
        # The other order: EEE1006F counts as EEE1008F, whose other offering is EEE1008S
        ("EEE1006F", 12, "EEE1008S", True),
        # MAM1000F counts as MAM1001F, which counts as MAM1002F: two equivalence steps
        ("MAM1000F", 18, "MAM1002F", False),
        # The same pass at 16 credits isn't the 18-credit PHY1013S, so there's no offering step
        ("PHY1013F", 16, "PHY1015S", False),
    ],
)
def test_a_pass_covers_one_equivalence_and_one_offering_away(
    code: str, credits: int, target: str, covered: bool
) -> None:
    rules = her_year(
        [course("PHY1013S", 18), course("PHY1015S", 18), course("EEE1008S", 12)],
        total=48,
        equivalences=[
            ("PHY1013S", "PHY1015S"),
            ("EEE1006F", "EEE1008F"),
            ("MAM1000F", "MAM1001F"),
            ("MAM1001F", "MAM1002F"),
        ],
    )
    assert (target in Covers(rules)(code, credits)) is covered


@pytest.mark.parametrize(
    ("needed", "expected"),
    [
        # AAA1001F runs in the first semester, as BBB1002F does, so the plan meets the
        # co-requisite
        ("AAA1001F", [{"AAA1001F", "BBB1002F"}]),
        # AAA1001S starts the semester after BBB1002F, too late to count, and the year needs
        # BBB1002F, so there's no plan
        ("AAA1001S", []),
    ],
)
def test_a_corequisite_in_the_plan_starts_no_later(
    needed: str, expected: list[set[str]]
) -> None:
    rule = {"course": needed, "need": "concurrent"}
    rules = her_year(
        [course(needed)], total=32, electives=[course("BBB1002F", rule=rule)]
    )
    checked = check(SHE, [], rules, SYMBOLS)
    assert [set(plan) for plan in checked.plans] == expected
    # Outside a plan she could take it alongside, so it's open either way
    assert checked.statuses["BBB1002F"] == "check"


@pytest.mark.parametrize(
    ("total", "expected"),
    [
        # One elective meets choose 1 and the 32 credits, so a plan with both has a spare
        (32, [{"AAA1001F", "BBB1002F"}, {"AAA1001F", "CCC1003F"}]),
        # 48 credits need both, so neither is spare
        (48, [{"AAA1001F", "BBB1002F", "CCC1003F"}]),
    ],
)
def test_a_plan_has_no_spare_elective(total: int, expected: list[set[str]]) -> None:
    rules = her_year(
        [course("AAA1001F")],
        total=total,
        electives=[course("BBB1002F"), course("CCC1003F")],
    )
    assert plans(rules) == expected


@pytest.mark.parametrize(
    ("days", "dropped", "expected"),
    [
        # She failed AAA1001F, which meets on Monday and Tuesday at 09:00. BBB1002F meets on
        # Monday at 09:00, so it's left out, and the 48-credit minimum falls by its 16 to the 32
        # the other two give.
        ((1, 3), {"BBB1002F"}, [{"AAA1001F", "CCC1003F"}]),
        # CCC1003F meets on Tuesday as well: two one-to-one clashes, so both are left out and the
        # minimum falls to AAA1001F's 16
        ((1, 2), {"BBB1002F", "CCC1003F"}, [{"AAA1001F"}]),
    ],
)
def test_a_repeated_course_takes_precedence(
    days: tuple[int, int], dropped: set[str], expected: list[set[str]]
) -> None:
    meetings = [
        meets("AAA1001F", 1, "09:00", "10:00"),
        meets("AAA1001F", 2, "09:00", "10:00"),
        meets("BBB1002F", days[0], "09:00", "10:00"),
        meets("CCC1003F", days[1], "09:00", "10:00"),
    ]
    rules = her_year(
        [course("AAA1001F"), course("BBB1002F"), course("CCC1003F")],
        total=48,
        meetings=meetings,
    )
    checked = check(SHE, [line("AAA1001F", "F", 40)], rules, SYMBOLS)
    assert checked.dropped == dropped
    assert [set(plan) for plan in checked.plans] == expected


@pytest.mark.parametrize(
    ("passed", "year"),
    [
        (set(), 1),  # nothing passed
        # One third-year course taken early doesn't move her up from second year
        ({"A1", "A2", "C1"}, 2),
        # Two do, and second year's core is then arrears
        ({"A1", "A2", "C1", "C2"}, 3),
        # A gap in first year is arrears: second year complete puts her in third
        ({"A1", "B1", "B2"}, 3),
        ({"A1", "A2", "B1", "B2", "C1", "C2", "C3"}, 4),  # every year complete
    ],
)
def test_her_year_of_study(passed: set[str], year: int) -> None:
    core = {1: {"A1", "A2"}, 2: {"B1", "B2"}, 3: {"C1", "C2", "C3"}}
    assert year_of_study(core, passed.__contains__) == year


def test_one_choice_of_sections_works_for_the_whole_plan_at_once() -> None:
    # Each course can meet on Monday at 09:00 or at 10:00. Any two fit, one at each hour, but
    # three can't share two hours.
    nine = (Meeting("sem1", 1, time(9), time(10)),)
    ten = (Meeting("sem1", 1, time(10), time(11)),)
    either = Week(choices=((nine, ten),))
    assert schedulable([either, either])
    assert not schedulable([either, either, either])


def test_a_slot_lists_what_fits_and_leaves_out_what_she_passed() -> None:
    # Two complementary lines, and DDD1004F, which she passed, fills one. GGG1005F fits only in
    # its section B on Tuesday, as section A meets on Monday with AAA1001F. HHH1006F meets on
    # Monday too, with no other section. The minimum is 52, less the 18 of the line filled: the
    # 16 of AAA1001F and the 18 of the slot.
    meetings = [
        meets("AAA1001F", 1, "09:00", "10:00"),
        meets("GGG1005F", 1, "09:00", "10:00", choice="A"),
        meets("GGG1005F", 2, "09:00", "10:00", choice="B"),
        meets("HHH1006F", 1, "09:30", "10:30"),
    ]
    complementary = [
        course("DDD1004F", 18),
        course("GGG1005F", 18),
        course("HHH1006F", 18),
    ]
    rules = her_year(
        [course("AAA1001F")],
        total=52,
        lines=(18, 18),
        complementary=complementary,
        meetings=meetings,
    )
    checked = check(SHE, [line("DDD1004F", "1", 75, credits=18)], rules, SYMBOLS)
    assert checked.slots == {
        frozenset({"AAA1001F"}): (Slot(18, None, frozenset({"GGG1005F"})),)
    }
