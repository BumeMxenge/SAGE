# Checks the plan stand-in: it reads its seed file as it's built, and gives a student Mbali's plan
# set, unanswered and with nothing hidden, with the ids sage seed would make
from uuid import UUID

import pytest

from sage.domain.rules import RuleSet
from sage.domain.students import Student
from sage.services.seed import load_seed
from sage.services.stubs import SeededPlanGenerator

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
