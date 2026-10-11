# Checks the seed file loads into the domain types and reads back unchanged through the fakes
import json
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

from sage.adapters.memory.rules import InMemoryRuleRepository
from sage.adapters.memory.students import InMemoryStudentRepository
from sage.services.seed import counts, load_seed, seed

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


def test_student_ids_follow_the_account_but_slot_ids_do_not(seed_file):
    mine, theirs = load_seed(seed_file, ACCOUNT), load_seed(seed_file, OTHER_ACCOUNT)
    assert {p.id for p in mine.student.plans}.isdisjoint(
        p.id for p in theirs.student.plans
    )
    assert mine.rules.timetable_slots == theirs.rules.timetable_slots
    assert len({slot.id for slot in mine.rules.timetable_slots}) == 25


def test_rows_belong_to_the_account(seed_file):
    student = load_seed(seed_file, ACCOUNT).student
    assert student.student.id == ACCOUNT
    assert {row.student_id for row in student.plan_courses} == {ACCOUNT}


def test_chat_pairs_are_stored_lowest_id_first(seed_file):
    chats = load_seed(seed_file, ACCOUNT).student.chats
    pairs = [chat for chat in chats if chat.other_plan_id is not None]
    assert pairs
    assert all(chat.plan_id < chat.other_plan_id for chat in pairs)


def test_plan_courses_take_the_year_of_their_plan_set(seed_file, tmp_path):
    student = load_seed(seed_file, ACCOUNT).student
    assert {row.handbook_year for row in student.plan_courses} == {2026}

    def wrong_year(data):
        data["plan_courses"][0]["handbook_year"] = 2025

    with pytest.raises(ValueError, match="plan set's year"):
        load_seed(edited_copy(seed_file, tmp_path, wrong_year), ACCOUNT)


def test_her_made_up_identity_stays_out_of_her_data(seed_file):
    data = load_seed(seed_file, ACCOUNT)
    assert data.fake_account.name == "Mbali Dlamini"
    assert "Mbali" not in data.student.model_dump_json()


def test_an_unknown_category_is_refused(seed_file, tmp_path):
    def cooking(data):
        data["course_group_members"][-1]["category"] = "cooking"

    with pytest.raises(ValidationError):
        load_seed(edited_copy(seed_file, tmp_path, cooking), ACCOUNT)


def test_a_misspelt_column_is_refused(seed_file, tmp_path):
    def misspelt(data):
        data["courses"][0]["credit"] = data["courses"][0].pop("credits")

    with pytest.raises(ValidationError):
        load_seed(edited_copy(seed_file, tmp_path, misspelt), ACCOUNT)


def test_the_fakes_give_back_what_was_seeded(seed_file):
    rules, students = InMemoryRuleRepository(), InMemoryStudentRepository()
    data = load_seed(seed_file, ACCOUNT)
    first = seed(rules, students, data)
    again = seed(rules, students, data)
    assert first.rulebook_differences == first.student_differences == ()
    assert again == first
    assert students.get(ACCOUNT) == data.student
