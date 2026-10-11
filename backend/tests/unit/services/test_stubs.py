# Checks the stand-ins. The plan one reads its seed file as it's built, and gives a student Mbali's
# plan set, unanswered and with nothing hidden, with the ids sage seed would make. The eligibility
# one applies its rules in order, and leaves a rule it can't read to her advisor
from uuid import UUID

import pytest

from sage.domain.rules import ResultSymbol, RuleSet
from sage.domain.students import CourseHistoryLine, Student
from sage.services.seed import load_seed
from sage.services.stubs import UNCHECKED, InterimEligibility, SeededPlanGenerator

STUDENT = Student(id=UUID(int=7))


def test_a_missing_seed_file_stops_it_at_once(tmp_path):
    with pytest.raises(FileNotFoundError):
        SeededPlanGenerator(tmp_path / "mbali.json")


def test_it_gives_mbalis_set_unanswered_and_all_visible(seed_file):
    rows = SeededPlanGenerator(seed_file).generate(STUDENT, [], RuleSet())
    seeded = load_seed(seed_file, STUDENT.id).student
    assert rows.plan_set.id == seeded.plan_sets[0].id
    assert (rows.plan_set.answers, rows.plan_set.complete) == (None, False)
    assert [plan.id for plan in rows.plans] == [plan.id for plan in seeded.plans]
    assert not any(plan.hidden for plan in rows.plans)
    assert (len(rows.plan_courses), len(rows.plan_reasons)) == (80, 6)


@pytest.fixture
def rules(seed_file) -> RuleSet:
    # Mbali's 2026 rulebook, which the API checks entry requirements against
    return load_seed(seed_file, UUID(int=1)).rules


@pytest.fixture
def symbols(result_symbols) -> dict[str, ResultSymbol]:
    return {symbol.symbol: symbol for symbol in result_symbols}


def test_an_entry_rule_it_cant_check_says_to_ask_her_advisor(rules, symbols):
    # EEE4117F's rule needs a pass in EEE3091F, so it's neither empty nor a printed refer
    verdict = InterimEligibility().check(rules.courses, [], rules, symbols)["EEE4117F"]
    assert (verdict.status, verdict.reason) == ("check", UNCHECKED)


def test_a_course_she_passed_is_not_eligible_whatever_its_entry_rule(rules, symbols):
    passed = CourseHistoryLine(
        student_id=STUDENT.id,
        academic_year=2025,
        term="sem1",
        course_code="EEE4117F",
        course_name="Energy Conversion II",
        credits=16,
        nqf_level=8,
        result="1",
        mark=75,
    )
    verdicts = InterimEligibility().check(rules.courses, [passed], rules, symbols)
    assert verdicts["EEE4117F"].status == "not_eligible"
