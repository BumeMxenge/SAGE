# Checks the seed file loads into the domain types, is written only once her plans' year is loaded,
# and reads back unchanged through the fakes
import json
from pathlib import Path
from uuid import UUID

import pytest

from sage.adapters.memory.rules import InMemoryRuleRepository
from sage.adapters.memory.students import InMemoryStudentRepository
from sage.domain.rules import HandbookVersion, RuleSet
from sage.services.seed import YearNotLoaded, counts, load_seed, seed

# Made-up account ids, standing in for two sign-in accounts
ACCOUNT = UUID("00000000-0000-4000-8000-000000000001")
OTHER_ACCOUNT = UUID("00000000-0000-4000-8000-000000000002")


def edited_copy(seed_file: Path, tmp_path: Path, edit) -> Path:
    data = json.loads(seed_file.read_text(encoding="utf-8"))
    edit(data)
    copy = tmp_path / "seed.json"
    copy.write_text(json.dumps(data), encoding="utf-8")
    return copy


def test_counts_match_the_mbali_table(seed_file, mbali_counts):
    assert counts(load_seed(seed_file, ACCOUNT)) == mbali_counts


def test_every_run_makes_the_same_ids(seed_file):
    assert load_seed(seed_file, ACCOUNT) == load_seed(seed_file, ACCOUNT)


def test_ids_follow_the_account(seed_file):
    mine, theirs = load_seed(seed_file, ACCOUNT), load_seed(seed_file, OTHER_ACCOUNT)
    assert {p.id for p in mine.plans}.isdisjoint(p.id for p in theirs.plans)


def test_her_plans_and_hearts_name_only_approved_2026_courses(seed_file, approved_2026):
    # So an approval that drops one of her courses fails here, before a plan or a heart points at
    # nothing. Her history keeps its own codes, which the year's equivalences cover.
    student = load_seed(seed_file, ACCOUNT)
    named = {row.course_code for row in (*student.plan_courses, *student.favourites)}
    assert named <= {course.code for course in approved_2026.courses}


def test_rows_belong_to_the_account(seed_file):
    student = load_seed(seed_file, ACCOUNT)
    assert student.student.id == ACCOUNT
    assert {row.student_id for row in student.plan_courses} == {ACCOUNT}


def test_chat_pairs_are_stored_lowest_id_first(seed_file):
    chats = load_seed(seed_file, ACCOUNT).chats
    pairs = [chat for chat in chats if chat.other_plan_id is not None]
    assert pairs
    assert all(chat.plan_id < chat.other_plan_id for chat in pairs)


def test_plan_courses_take_the_year_of_their_plan_set(seed_file, tmp_path):
    student = load_seed(seed_file, ACCOUNT)
    assert {row.handbook_year for row in student.plan_courses} == {2026}

    def wrong_year(data):
        data["plan_courses"][0]["handbook_year"] = 2025

    with pytest.raises(ValueError, match="plan set's year"):
        load_seed(edited_copy(seed_file, tmp_path, wrong_year), ACCOUNT)


def misspelt(data):
    line = data["course_history"][0]
    line["credit"] = line.pop("credits")


def with_rules(data):
    # As an older seed file held them, though only sage load writes rules now
    data["courses"] = []


@pytest.mark.parametrize(
    ("edit", "named"),
    [(misspelt, "credit"), (with_rules, "courses")],
    ids=["a misspelt column", "a rule table"],
)
def test_what_the_seed_doesnt_know_is_refused(seed_file, tmp_path, edit, named):
    # A ValidationError is a ValueError too
    with pytest.raises(ValueError, match=named):
        load_seed(edited_copy(seed_file, tmp_path, edit), ACCOUNT)


def test_the_fakes_give_back_what_was_seeded(seed_file, approved_2026):
    rules, students = InMemoryRuleRepository(), InMemoryStudentRepository()
    rules.replace_year(approved_2026)
    data = load_seed(seed_file, ACCOUNT)
    first = seed(rules, students, data)
    again = seed(rules, students, data)
    assert first.student_differences == ()
    assert again == first
    # Compared as written: the fake stamps each chat and message with a time, as the database does
    assert students.get(ACCOUNT).model_dump() == data.model_dump()


@pytest.mark.parametrize(
    "held", [(), (HandbookVersion(year=2026),)], ids=["not loaded", "loaded partway"]
)
def test_nothing_is_written_until_her_plans_year_is_approved(seed_file, held):
    # A load that stops partway leaves its year unapproved, so that counts as not loaded
    rules, students = InMemoryRuleRepository(), InMemoryStudentRepository()
    for version in held:
        rules.replace_year(RuleSet(handbook_versions=(version,)))
    with pytest.raises(YearNotLoaded, match="2026"):
        seed(rules, students, load_seed(seed_file, ACCOUNT))
    assert students.get(ACCOUNT) is None
