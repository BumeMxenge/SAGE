# The same checks against the in-memory fake and against local Supabase, so the fake the unit tests
# use can't drift from the real thing. The fake's half runs with the unit tests; the Supabase half
# needs make check-db.
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest

from sage.adapters.memory.rules import InMemoryRuleRepository
from sage.adapters.memory.students import InMemoryStudentRepository
from sage.domain.repositories import RuleRepository, StudentRepository
from sage.domain.students import Student
from sage.services.seed import Seed, load_seed, seed
from sage.services.stubs import SeededPlanGenerator


@dataclass(frozen=True)
class Store:
    rules: RuleRepository
    students: StudentRepository
    mbali: Seed  # seeded on her account, with the ids it was stored with
    stranger: UUID  # an account with nothing stored


@pytest.fixture(
    params=["memory", pytest.param("supabase", marks=pytest.mark.integration)]
)
def store(request, seed_file, result_symbols) -> Store:
    if request.param == "memory":
        rules = InMemoryRuleRepository(result_symbols)
        students = InMemoryStudentRepository()
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


def test_the_current_year_is_the_latest_approved_one(store):
    assert store.rules.current_year() == 2026


def test_the_symbols_are_ucts_26(store, result_symbols):
    assert set(store.rules.symbols()) == set(result_symbols)


def test_a_saved_profile_reads_back_and_saving_again_updates_it(store):
    profile = Student(id=store.stranger, curriculum_code="EB011EEE05", intake_year=2024)
    store.students.save_profile(profile)
    assert store.students.profile(store.stranger) == profile
    done = profile.model_copy(update={"onboarding_complete": True})
    store.students.save_profile(done)
    assert store.students.profile(store.stranger) == done


def test_replacing_her_history_leaves_exactly_the_new_lines(store):
    her = store.mbali.student
    kept = her.course_history[:3]
    store.students.replace_history(her.student.id, kept)
    assert set(store.students.get(her.student.id).course_history) == set(kept)


def test_her_current_set_is_her_seeded_one_and_a_stranger_has_none(store):
    her = store.mbali.student
    current = store.students.current_plan_set(her.student.id)
    assert current.plan_set == her.plan_sets[0]
    assert [plan.position for plan in current.plans] == list(range(1, 11))
    assert set(current.plan_courses) == set(her.plan_courses)
    assert set(current.plan_reasons) == set(her.plan_reasons)
    assert store.students.current_plan_set(store.stranger) is None


def test_a_generated_set_is_written_complete_and_once(store, seed_file):
    store.students.save_profile(Student(id=store.stranger))
    rows = SeededPlanGenerator(seed_file).generate(
        Student(id=store.stranger), [], store.rules.get(2026)
    )
    store.students.add_plan_set(rows)
    store.students.add_plan_set(rows)  # as a retry would
    current = store.students.current_plan_set(store.stranger)
    assert current.plan_set.complete
    assert [plan.id for plan in current.plans] == [plan.id for plan in rows.plans]
    assert len(store.students.get(store.stranger).plan_sets) == 1


def test_plans_by_id_bring_their_set_and_reasons_and_only_hers(store):
    her = store.mbali.student
    by_position = {plan.position: plan for plan in her.plans}
    (rows,) = store.students.plans(her.student.id, [by_position[7].id])
    assert rows.plan_set == her.plan_sets[0]
    assert rows.plans == (by_position[7],)
    assert len(rows.plan_courses) == 8
    # The set's five reasons, then the plan's own
    assert [reason.plan_id for reason in rows.plan_reasons] == [None] * 5 + [
        by_position[7].id
    ]
    both = store.students.plans(her.student.id, [by_position[1].id, by_position[2].id])
    assert {rows.plans[0].position for rows in both} == {1, 2}
    assert store.students.plans(store.stranger, [by_position[7].id]) == ()
