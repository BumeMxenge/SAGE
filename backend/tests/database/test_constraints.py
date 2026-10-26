# Checks the database refuses rows that break its rules, even from the backend's secret key. A test
# that has to add rows removes them again before it asserts anything, in a finally, so a failure
# never leaves them in the local database every worktree shares.
from datetime import datetime
from uuid import uuid4

import pytest
from postgrest import APIError

pytestmark = pytest.mark.integration

FOREIGN_KEY, CHECK = "23503", "23514"
# A real 2026 course and term, for rows that need one, so a test using it asks for the loaded years
SLOT = {"handbook_year": 2026, "course_code": "EEE4113F", "term": "sem1"}


def test_a_row_cannot_point_at_another_students_plan_or_chat(
    secret, mbali, stranger, refused
):
    plan_course = {
        "plan_id": str(mbali.plans[0].id),
        "student_id": str(stranger.id),
        "course_code": "HUB4049F",  # a real 2026 course that isn't in her first plan
        "handbook_year": 2026,
    }
    refused(
        secret.table("plan_courses").insert(plan_course),
        FOREIGN_KEY,
        "plan_courses_plan_id_student_id_fkey",
    )
    message = {
        "chat_id": str(mbali.chats[0].id),
        "student_id": str(stranger.id),
        "role": "user",
        "content": "Hi",
    }
    refused(
        secret.table("messages").insert(message),
        FOREIGN_KEY,
        "messages_chat_id_student_id_fkey",
    )


def test_a_compared_pair_stored_in_the_wrong_order_is_refused(secret, mbali, refused):
    low, high = sorted(plan.id for plan in mbali.plans[:2])
    chat = {
        "student_id": str(mbali.student.id),
        "plan_id": str(high),
        "other_plan_id": str(low),
    }
    refused(secret.table("chats").insert(chat), CHECK)


def test_an_unknown_result_symbol_is_refused(secret, mbali, refused):
    line = {
        "student_id": str(mbali.student.id),
        "academic_year": 2025,
        "term": "sem1",
        "course_code": "TST1000F",
        "course_name": "Test",
        "credits": 0,
        "result": "ZZ",
    }
    refused(
        secret.table("course_history").insert(line),
        FOREIGN_KEY,
        "course_history_result_fkey",
    )


# The link names one of 2026's slots, so 2026 must be loaded for the refusal to be the curriculum's
@pytest.mark.usefixtures("approved_years")
def test_a_slot_curriculum_must_be_in_its_slots_year(secret, approved_2026):
    curriculum = {
        "handbook_year": 2099,
        "code": "EB011EEE05",
        "name": "Test",
        "department": "Test",
    }
    link = {
        "slot_id": str(approved_2026.timetable_slots[0].id),
        "handbook_year": 2099,
        "curriculum_code": "EB011EEE05",
    }
    secret.table("handbook_versions").insert({"year": 2099}).execute()
    try:
        secret.table("curricula").insert(curriculum).execute()
        with pytest.raises(APIError) as error:
            secret.table("timetable_slot_curricula").insert(link).execute()
    finally:
        secret.table("handbook_versions").delete().eq("year", 2099).execute()
    # Refused by the link that keeps the year equal to the slot's, not by the curriculum link
    assert error.value.code == FOREIGN_KEY
    assert "slot_id_handbook_year" in error.value.message


def test_a_reason_names_only_a_plan_in_its_own_set(secret, mbali):
    student_id = str(mbali.student.id)
    plan_set = {"student_id": student_id, "period": 2026, "version": 2}
    other_set = secret.table("plan_sets").insert(plan_set).execute().data[0]["id"]
    reason = {
        "plan_set_id": other_set,
        "student_id": student_id,
        "kind": "included",
        "message": "Test",
    }
    naming_a_plan = reason | {"plan_id": str(mbali.plans[0].id)}
    try:
        with pytest.raises(APIError) as error:
            secret.table("plan_reasons").insert(naming_a_plan).execute()
        whole_set = secret.table("plan_reasons").insert(reason).execute().data
    finally:
        secret.table("plan_sets").delete().eq(
            "id", other_set
        ).execute()  # and its reasons
    assert error.value.code == FOREIGN_KEY
    assert len(whole_set) == 1


def test_two_messages_sent_together_get_increasing_times(secret, mbali):
    chat = mbali.chats[0]
    turn = {
        "chat_id": str(chat.id),
        "student_id": str(chat.student_id),
        "role": "user",
        "content": "Test",
    }
    stored = secret.table("messages").insert([turn, turn]).execute().data
    secret.table("messages").delete().in_("id", [row["id"] for row in stored]).execute()
    first, second = (datetime.fromisoformat(row["created_at"]) for row in stored)
    assert first < second


@pytest.mark.usefixtures("approved_years")
def test_a_slot_with_a_start_but_no_end_is_refused(secret, refused):
    slot = SLOT | {"start_time": "08:00"}
    refused(secret.table("timetable_slots").insert(slot), CHECK)


@pytest.mark.usefixtures("approved_years")
def test_a_slot_with_times_but_no_day_is_kept(secret):
    slot = SLOT | {"start_time": "08:00", "end_time": "08:45"}
    stored = secret.table("timetable_slots").insert(slot).execute().data[0]
    secret.table("timetable_slots").delete().eq("id", stored["id"]).execute()
    assert stored["day"] is None


def test_only_a_reply_can_refer_or_offer_a_plan(secret, mbali, refused):
    chat = mbali.chats[0]
    question = {
        "chat_id": str(chat.id),
        "student_id": str(chat.student_id),
        "role": "user",
        "content": "Test",
    }
    refused(secret.table("messages").insert(question | {"referral": True}), CHECK)
    offer = {"open_plan_id": str(chat.plan_id)}
    refused(secret.table("messages").insert(question | offer), CHECK)


def test_deleting_the_plan_a_reply_offers_clears_the_offer(secret, mbali):
    # The offered plan sits in a set of its own, so deleting it leaves her seeded plans alone
    student_id = str(mbali.student.id)
    plan_set = {"student_id": student_id, "period": 2026, "version": 3}
    set_id = secret.table("plan_sets").insert(plan_set).execute().data[0]["id"]
    reply_id = str(uuid4())  # known before it's stored, so the finally can remove it
    plan = {
        "plan_set_id": set_id,
        "student_id": student_id,
        "position": 1,
        "name": "Test",
    }
    try:
        plan_id = secret.table("plans").insert(plan).execute().data[0]["id"]
        reply = {
            "id": reply_id,
            "chat_id": str(mbali.chats[0].id),
            "student_id": student_id,
            "role": "assistant",
            "content": "Test",
            "open_plan_id": plan_id,
        }
        secret.table("messages").insert(reply).execute()
        secret.table("plan_sets").delete().eq("id", set_id).execute()  # and its plan
        query = secret.table("messages").select("open_plan_id").eq("id", reply_id)
        after = query.execute().data
    finally:
        secret.table("plan_sets").delete().eq("id", set_id).execute()
        secret.table("messages").delete().eq("id", reply_id).execute()
    assert after == [{"open_plan_id": None}]
