# Checks the stand-ins. The plan one reads its seed file as it's built, and gives a student Mbali's
# plan set, unanswered and with nothing hidden, with the ids sage seed would make. The eligibility
# one applies its rules in order, and leaves a rule it can't read to her advisor. The advisor one
# hands every question to a human advisor.
from uuid import UUID, uuid4

import pytest

from sage.engine.stubs import (
    FIXED_REPLY,
    UNCHECKED,
    FixedAdvisor,
    InterimEligibility,
    SeededPlanGenerator,
)
from sage.shared.advisor import Reply
from sage.shared.rules import ResultSymbol, RuleSet
from sage.shared.seed import load_seed
from sage.shared.students import Chat, CourseHistoryLine, Student

STUDENT = Student(id=UUID(int=7))


@pytest.mark.stub("engine")
def test_a_missing_seed_file_stops_it_at_once(tmp_path):
    with pytest.raises(FileNotFoundError):
        SeededPlanGenerator(tmp_path / "mbali.json")


@pytest.mark.stub("engine")
def test_it_gives_mbalis_set_unanswered_and_all_visible(seed_file):
    rows = SeededPlanGenerator(seed_file).generate(STUDENT, [], RuleSet())
    seeded = load_seed(seed_file, STUDENT.id)
    assert rows.plan_set.id == seeded.plan_sets[0].id
    assert (rows.plan_set.answers, rows.plan_set.complete) == (None, False)
    assert [plan.id for plan in rows.plans] == [plan.id for plan in seeded.plans]
    assert not any(plan.hidden for plan in rows.plans)
    assert (len(rows.plan_courses), len(rows.plan_reasons)) == (80, 6)


@pytest.fixture
def symbols(result_symbols) -> dict[str, ResultSymbol]:
    return {symbol.symbol: symbol for symbol in result_symbols}


def line(code: str, result: str) -> CourseHistoryLine:
    # One line of her record, as her transcript would give it
    return CourseHistoryLine(
        student_id=STUDENT.id,
        academic_year=2025,
        term="sem1",
        course_code=code,
        course_name="Made Up",
        credits=16,
        result=result,
    )


def verdict(
    rules: RuleSet, symbols, history: list[CourseHistoryLine], code: str
) -> tuple[str, str | None]:
    # What the stand-in says of one course, checked against the approved 2026
    found = InterimEligibility().check(rules.courses, history, rules, symbols)[code]
    return found.status, found.reason


@pytest.mark.stub("engine")
def test_an_entry_rule_it_cant_check_says_to_ask_her_advisor(approved_2026, symbols):
    # p. 139 prints EEE4117F's requirement as EEE3091F, so it's neither empty nor a printed refer
    assert verdict(approved_2026, symbols, [], "EEE4117F") == ("check", UNCHECKED)


@pytest.mark.stub("engine")
def test_a_course_she_passed_is_not_eligible_whatever_its_entry_rule(
    approved_2026, symbols
):
    assert verdict(approved_2026, symbols, [line("EEE4117F", "1")], "EEE4117F") == (
        "not_eligible",
        "You've already passed EEE4117F.",
    )


@pytest.mark.stub("engine")
def test_a_failed_course_doesnt_count(approved_2026, symbols):
    # So EEE4117F's rule still decides, which it can't check
    assert verdict(approved_2026, symbols, [line("EEE4117F", "F")], "EEE4117F") == (
        "check",
        UNCHECKED,
    )


@pytest.mark.stub("engine")
def test_a_course_that_a_pass_counts_as_is_not_eligible_either(approved_2026, symbols):
    # The approved 2026 equivalences say EEE1006F counts as EEE1008F, which took its first-year
    # slot (2023 p. 46, 2026 p. 48). p. 129 prints no requirement for EEE1008F, so without the
    # equivalence it would be open to her.
    assert verdict(approved_2026, symbols, [line("EEE1006F", "3")], "EEE1008F") == (
        "not_eligible",
        "You've already passed EEE1006F.",
    )


@pytest.mark.stub("advisor")
def test_the_fixed_reply_refers_her_and_offers_a_pairs_second_plan():
    pair = Chat(
        id=uuid4(), student_id=STUDENT.id, plan_id=uuid4(), other_plan_id=uuid4()
    )
    assert FixedAdvisor().reply(pair, "Which plan?", "sem1") == Reply(
        content=FIXED_REPLY, referral=True, open_plan_id=pair.other_plan_id
    )
    alone = pair.model_copy(update={"other_plan_id": None})
    assert FixedAdvisor().reply(alone, "Which plan?", "sem1").open_plan_id is None
