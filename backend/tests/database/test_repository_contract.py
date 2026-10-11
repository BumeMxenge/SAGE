# The same checks against the in-memory fake and against local Supabase, so the fake the unit tests
# use can't drift from the real thing. The fake's half runs with the unit tests; the Supabase half
# needs make check-db.
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest

from sage.adapters.memory.rules import InMemoryRuleRepository
from sage.adapters.memory.students import InMemoryStudentRepository
from sage.domain.repositories import RuleRepository, StudentRepository
from sage.services.seed import Seed, load_seed, seed


@dataclass(frozen=True)
class Store:
    rules: RuleRepository
    students: StudentRepository
    mbali: Seed  # seeded on her account, with the ids it was stored with
    stranger: UUID  # an account with nothing stored


@pytest.fixture(
    params=["memory", pytest.param("supabase", marks=pytest.mark.integration)]
)
def store(request, seed_file) -> Store:
    if request.param == "memory":
        rules, students = InMemoryRuleRepository(), InMemoryStudentRepository()
        her, stranger = uuid4(), uuid4()
    else:
        rules, students = request.getfixturevalue("stores")
        new_account = request.getfixturevalue("new_account")
        her, stranger = new_account().id, new_account().id
    mbali = load_seed(seed_file, her)
    seed(rules, students, mbali)
    return Store(rules, students, mbali, stranger)


def test_profile_reads_her_row_and_nothing_for_a_stranger(store):
    her = store.mbali.student.student
    assert store.students.profile(her.id) == her
    assert store.students.profile(store.stranger) is None
