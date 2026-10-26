# Checks the evaluator's three values on rules built for each test, worked out by hand from the
# decisions they follow: all and any around a printed refer, a mark at and beside its threshold,
# results still to come, covers and passes counted once, and the leaves that read her curriculum
# and her year
from uuid import UUID

import pytest

from sage.engine.evaluator import Record, evaluate
from sage.shared.rules import (
    AllOf,
    AllOfGroup,
    AnyOf,
    Course,
    CourseGroupMember,
    CourseNeed,
    CurriculumRule,
    Equivalence,
    MinYearOfStudy,
    Refer,
    RuleSet,
    StudentIn,
    TotalCredits,
    YearRules,
)
from sage.shared.students import CourseHistoryLine, Student

STUDENT = Student(id=UUID(int=7), curriculum_code="EB000AAA01", intake_year=2024)
REFER = Refer(refer="At least 70% for NSC Mathematics.")
NO_RULES = RuleSet()


@pytest.fixture
def symbols(result_symbols):
    return {row.symbol: row for row in result_symbols}


def line(code: str, result: str, mark: int | None = None, credits: int = 16):
    return CourseHistoryLine(
        student_id=STUDENT.id,
        academic_year=2025,
        term="sem1",
        course_code=code,
        course_name="Made Up",
        credits=credits,
        result=result,
        mark=mark,
    )


def need(code: str, kind: str = "pass", mark: int | None = None) -> CourseNeed:
    return CourseNeed(course=code, need=kind, min_mark=mark)


def value(rule, lines, symbols, rules: RuleSet = NO_RULES) -> str:
    return evaluate(rule, Record(STUDENT, lines, rules, symbols)).value


@pytest.mark.parametrize(
    ("kind", "result", "expected"),
    [
        # all holds only when every part does, so the refer keeps it open unless the other part fails
        ("all", "1", "open"),
        ("all", "F", "not_met"),
        ("all", "OS", "open"),
        # any holds when either part does, and otherwise the refer keeps it open
        ("any", "1", "met"),
        ("any", "F", "open"),
        ("any", "OS", "open"),
    ],
)
def test_all_and_any_around_a_refer(kind, result, expected, symbols):
    other = need("AAA1000F")
    rule = AllOf(all=(REFER, other)) if kind == "all" else AnyOf(any=(REFER, other))
    assert value(rule, [line("AAA1000F", result)], symbols) == expected


@pytest.mark.parametrize(
    ("result", "mark", "min_mark", "expected"),
    [
        ("2-", 60, 60, "met"),  # exactly the mark meets it
        ("3", 59, 60, "not_met"),
        ("F", 47, 45, "met"),  # a failed course's mark still counts
        ("FS", 47, 50, "open"),  # a supplementary still to come could reach 50
        ("FS", 47, 51, "not_met"),  # but no more
        (
            "SP",
            None,
            50,
            "met",
        ),  # a supplementary pass counts as 50, as the Term GPA has it
        ("SP", None, 51, "not_met"),
        ("CR", None, 50, "open"),  # credit carries no mark
        ("PA", None, 50, "open"),  # nor does a pass printed without one
        ("OS", None, 50, "open"),  # and a result still to come has none yet
    ],
)
def test_a_mark_leaf(result, mark, min_mark, expected, symbols):
    rule = need("AAA1000F", "mark", min_mark)
    assert value(rule, [line("AAA1000F", result, mark)], symbols) == expected


@pytest.mark.parametrize(
    ("passed", "expected"), [((), "not_met"), (("AAA1001F",), "met")]
)
def test_an_any_fails_only_when_every_branch_does(passed, expected, symbols):
    rule = AnyOf(any=(need("AAA1000F"), need("AAA1001F")))
    assert value(rule, [line(code, "1") for code in passed], symbols) == expected


def test_an_equivalence_meets_the_course_it_counts_as(symbols):
    # The approved 2026 has EEE1006F count as EEE1008F, which took its first-year slot
    rules = RuleSet(
        equivalences=(
            Equivalence(
                handbook_year=2026, course_code="EEE1006F", counts_as="EEE1008F"
            ),
        )
    )
    lines = [line("EEE1006F", "3", 59, credits=12)]
    assert value(need("EEE1008F"), lines, symbols, rules) == "met"


@pytest.mark.parametrize(("credits", "expected"), [(18, "met"), (15, "not_met")])
def test_one_semesters_offering_covers_the_other_at_the_same_credits(
    credits, expected, symbols
):
    # The 2026 rules hold ECO1010S at 18 credits, as her ECO1010F was, so her pass covers it
    rules = RuleSet(
        courses=(
            Course(
                handbook_year=2026,
                code="ECO1010S",
                name="Microeconomics",
                credits=credits,
                nqf_level=5,
                term="sem2",
            ),
        )
    )
    lines = [line("ECO1010F", "1", 80, credits=18)]
    assert value(need("ECO1010S"), lines, symbols, rules) == expected


def offering(code: str, term: str) -> Course:
    return Course(
        handbook_year=2026,
        code=code,
        name="Made Up",
        credits=18,
        nqf_level=5,
        term=term,
    )


def counts(code: str, counts_as: str) -> Equivalence:
    return Equivalence(handbook_year=2026, course_code=code, counts_as=counts_as)


@pytest.mark.parametrize(
    ("taken", "rules", "leaf", "expected"),
    [
        # The approved 2026 holds PHY1014F, PHY1014S's other offering, at 18 credits, as her pass
        # was, and has it count as PHY1012F
        (
            "PHY1014S",
            RuleSet(
                courses=(offering("PHY1014F", "sem1"),),
                equivalences=(counts("PHY1014F", "PHY1012F"),),
            ),
            "PHY1012F",
            "met",
        ),
        # The other way round: an equivalence, then the other offering of what it counts as
        (
            "AAA1000F",
            RuleSet(
                courses=(offering("BBB1000S", "sem2"),),
                equivalences=(counts("AAA1000F", "BBB1000F"),),
            ),
            "BBB1000S",
            "met",
        ),
        # Never two equivalences
        (
            "AAA1000F",
            RuleSet(
                equivalences=(
                    counts("AAA1000F", "BBB1000F"),
                    counts("BBB1000F", "CCC1000F"),
                )
            ),
            "CCC1000F",
            "not_met",
        ),
    ],
)
def test_a_cover_takes_one_equivalence_and_one_offering_step(
    taken, rules, leaf, expected, symbols
):
    lines = [line(taken, "1", 72, credits=18)]
    assert value(need(leaf), lines, symbols, rules) == expected


def test_a_pass_moves_to_another_code_it_covers_so_both_count(symbols):
    # Her older AAA1000F pass covers AAA1000F and its other offering, AAA1000S, and her BBB1000F
    # pass, at other credits, counts as AAA1000S alone. AAA1000S takes the older pass first, then
    # moves to the BBB1000F one, so AAA1000F counts too.
    rules = RuleSet(
        courses=(offering("AAA1000F", "sem1"), offering("AAA1000S", "sem2")),
        equivalences=(counts("BBB1000F", "AAA1000S"),),
    )
    older = line("AAA1000F", "1", 72, credits=18).model_copy(
        update={"academic_year": 2024}
    )
    lines = [older, line("BBB1000F", "1", 72, credits=16)]
    record = Record(STUDENT, lines, rules, symbols)
    assert record.counted(["AAA1000S", "AAA1000F"]) == ["AAA1000S", "AAA1000F"]


@pytest.mark.parametrize(
    ("curricula", "expected"),
    [(("EB000AAA01", "EB000BBB01"), "met"), (("EB000BBB01",), "not_met")],
)
def test_student_in_reads_her_curriculum(curricula, expected, symbols):
    assert value(StudentIn(student_in=curricula), [], symbols) == expected


@pytest.mark.parametrize(("year", "expected"), [(2, "met"), (3, "not_met")])
def test_min_year_of_study_either_side_of_her_year(year, expected, symbols):
    # Her first year's core is done and her second year's isn't, so she's in her second year
    rules = RuleSet(
        course_group_members=tuple(
            CourseGroupMember(handbook_year=2026, group_key=group, course_code=code)
            for group, code in (("y1", "AAA1000F"), ("y2", "AAA2000F"))
        ),
        curriculum_rules=tuple(
            CurriculumRule(
                handbook_year=2026,
                curriculum_code=STUDENT.curriculum_code,
                year_of_study=number,
                rule=YearRules(
                    all=(
                        AllOfGroup(all_of_group=group),
                        TotalCredits(total_credits=16),
                    )
                ),
            )
            for number, group in ((1, "y1"), (2, "y2"))
        ),
    )
    rule = MinYearOfStudy(min_year_of_study=year)
    assert value(rule, [line("AAA1000F", "1")], symbols, rules) == expected


def cores(years: int) -> RuleSet:
    # A made-up curriculum whose years each hold three core courses, AAA<year>000F to AAA<year>002F
    return RuleSet(
        course_group_members=tuple(
            CourseGroupMember(
                handbook_year=2026, group_key=f"y{year}", course_code=f"AAA{year}00{n}F"
            )
            for year in range(1, years + 1)
            for n in range(3)
        ),
        curriculum_rules=tuple(
            CurriculumRule(
                handbook_year=2026,
                curriculum_code=STUDENT.curriculum_code,
                year_of_study=year,
                rule=YearRules(
                    all=(
                        AllOfGroup(all_of_group=f"y{year}"),
                        TotalCredits(total_credits=48),
                    )
                ),
            )
            for year in range(1, years + 1)
        ),
    )


@pytest.mark.parametrize(
    ("fourth", "year"),
    [
        # She owes AAA2002F from her second year and has passed two third-year core courses, so
        # she's in her third year. One fourth-year course taken early, as EEE4124C can be, doesn't
        # move her up.
        (["AAA4000F"], 3),
        # Two do
        (["AAA4000F", "AAA4001F"], 4),
    ],
)
def test_her_year_is_the_latest_she_has_passed_two_core_courses_from(
    fourth, year, symbols
):
    passed = ["AAA1000F", "AAA1001F", "AAA1002F", "AAA2000F", "AAA2001F"]
    passed += ["AAA3000F", "AAA3001F", *fourth]
    lines = [line(code, "1") for code in passed]
    assert Record(STUDENT, lines, cores(4), symbols).year == year


def test_practical_training_doesnt_hold_her_year_back(symbols):
    # Her third year's core also holds AAA3000X, practical training, which her record doesn't show
    # yet. It doesn't count, so with her first three years' other core passed she's in her fourth.
    rules = cores(4)
    training = CourseGroupMember(
        handbook_year=2026, group_key="y3", course_code="AAA3000X"
    )
    rules = rules.model_copy(
        update={"course_group_members": (*rules.course_group_members, training)}
    )
    lines = [line(f"AAA{year}00{n}F", "1") for year in (1, 2, 3) for n in range(3)]
    assert Record(STUDENT, lines, rules, symbols).year == 4


def test_a_co_requisite_passed_earlier_is_met_and_one_not_taken_is_open(symbols):
    # With no plan to read, she could still take it alongside
    rule = need("MAM1020F", "concurrent")
    assert value(rule, [line("MAM1020F", "1")], symbols) == "met"
    assert value(rule, [], symbols) == "open"
