# Checks Finish setup generates one plan set a year however often she presses it, from the lines she
# confirmed and that year's rules
from collections.abc import Mapping, Sequence
from uuid import UUID, uuid4

import pytest

from sage.features.onboarding import service as onboarding
from sage.shared.memory.rules import InMemoryRuleRepository
from sage.shared.memory.students import InMemoryStudentRepository
from sage.shared.rulebook import Rulebook
from sage.shared.rules import ResultSymbol, RuleSet
from sage.shared.seed import load_seed
from sage.shared.students import (
    CourseHistoryLine,
    PlanSet,
    PlanSetRows,
    Student,
    StudentState,
)

STUDENT = UUID(int=1)


class Generator:
    # Stands in for the engine: records every call, and gives each set new ids, so a second set
    # would show. The engine can't, as it makes the same ids from the same record every time.
    def __init__(self) -> None:
        self.calls: list[tuple[Sequence[CourseHistoryLine], RuleSet]] = []

    def generate(
        self,
        student: Student,
        history: Sequence[CourseHistoryLine],
        rules: RuleSet,
        symbols: Mapping[str, ResultSymbol],
    ) -> PlanSetRows:
        self.calls.append((history, rules))
        return PlanSetRows(
            plan_set=PlanSet(id=uuid4(), student_id=student.id, period=2026, version=1)
        )


@pytest.fixture
def setup(seed_file, result_symbols, approved_2026):
    # Her stores with the approved 2026 and nothing of hers, and the lines she confirms
    rules = InMemoryRuleRepository(result_symbols)
    rules.replace_year(approved_2026)
    history = load_seed(seed_file, STUDENT).course_history
    return InMemoryStudentRepository(), Rulebook(rules), history


def finish(setup, generator: Generator) -> None:
    students, rulebook, history = setup
    onboarding.complete(STUDENT, "EB011EEE05", history, students, rulebook, generator)


def test_finishing_setup_twice_generates_one_plan_set(setup):
    students, rulebook, history = setup
    generator = Generator()
    finish(setup, generator)
    finish(setup, generator)
    assert generator.calls == [(history, rulebook.year(2026))]
    assert len(students.get(STUDENT).plan_sets) == 1


def test_a_plan_set_from_an_earlier_year_gets_this_years_after_it(setup):
    students = setup[0]
    earlier = PlanSet(
        id=uuid4(), student_id=STUDENT, period=2025, version=1, complete=True
    )
    students.replace(StudentState(student=Student(id=STUDENT), plan_sets=(earlier,)))
    generator = Generator()
    finish(setup, generator)
    assert len(generator.calls) == 1
    assert [row.period for row in students.get(STUDENT).plan_sets] == [2025, 2026]
