# The same checks against the in-memory fake and against local Supabase, so the fake the unit tests
# use can't drift from the real thing. The fake's half runs with the unit tests; the Supabase half
# needs make check-db.
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest

from sage.shared.memory.rules import InMemoryRuleRepository
from sage.shared.memory.students import InMemoryStudentRepository
from sage.shared.repositories import RuleRepository, StudentRepository, YearInUse
from sage.shared.rules import Course, HandbookVersion, RuleSet
from sage.shared.seed import load_seed, seed
from sage.shared.students import (
    Chat,
    Citation,
    Message,
    PlanSetRows,
    Student,
    StudentRecord,
    StudentState,
)


@dataclass(frozen=True)
class Store:
    rules: RuleRepository
    students: StudentRepository
    mbali: StudentState  # seeded on her account, with the ids it was stored with
    stranger: UUID  # an account with nothing stored


@pytest.fixture(
    params=["memory", pytest.param("supabase", marks=pytest.mark.integration)]
)
def store(request, seed_file, result_symbols, approved_2026) -> Store:
    if request.param == "memory":
        rules = InMemoryRuleRepository(result_symbols)
        rules.replace_year(approved_2026)
        students = InMemoryStudentRepository()
        her, stranger = uuid4(), uuid4()
    else:
        rules, students = request.getfixturevalue("stores")
        new_account = request.getfixturevalue("new_account")
        her, stranger = new_account().id, new_account().id
    mbali = load_seed(seed_file, her)
    seed(rules, students, mbali)
    return Store(rules, students, mbali, stranger)


@pytest.fixture
def made_up_year(request):
    # A year no plan uses, which leaves local Supabase again once its test is over
    secret = (
        request.getfixturevalue("secret")
        if request.node.callspec.params["store"] == "supabase"
        else None
    )
    yield 2097
    if secret:
        secret.table("handbook_versions").delete().eq("year", 2097).execute()


def test_replacing_a_year_leaves_exactly_its_new_rows(store, made_up_year):
    def holding(*courses):
        return RuleSet(
            handbook_versions=(HandbookVersion(year=made_up_year, approved=True),),
            courses=tuple(
                Course(
                    handbook_year=made_up_year,
                    code=code,
                    name=name,
                    credits=8,
                    nqf_level=5,
                    term="sem1",
                )
                for code, name in courses
            ),
        )

    store.rules.replace_year(holding(("TST1001F", "Gone"), ("TST1002F", "Before")))
    # One course goes, one changes and one is new, in key order as the store reads them
    after = holding(("TST1002F", "After"), ("TST1003F", "New"))
    store.rules.replace_year(after)
    assert store.rules.get(made_up_year) == after


def test_profile_reads_her_row_and_nothing_for_a_stranger(store):
    her = store.mbali.student
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
    her = store.mbali
    kept = her.course_history[:3]
    store.students.replace_history(her.student.id, kept)
    assert set(store.students.get(her.student.id).course_history) == set(kept)


def test_her_current_set_is_her_seeded_one_and_a_stranger_has_none(store):
    her = store.mbali
    current = store.students.current_plan_set(her.student.id)
    assert current.plan_set == her.plan_sets[0]
    assert [plan.position for plan in current.plans] == list(range(1, 11))
    assert set(current.plan_courses) == set(her.plan_courses)
    assert set(current.plan_reasons) == set(her.plan_reasons)
    assert store.students.current_plan_set(store.stranger) is None


def test_a_generated_set_is_written_complete_and_once(store, seed_file):
    # Mbali's seeded set, made the stranger's and marked not yet complete, as a new set arrives
    seeded = load_seed(seed_file, store.stranger)
    rows = PlanSetRows(
        plan_set=seeded.plan_sets[0].model_copy(update={"complete": False}),
        plans=seeded.plans,
        plan_courses=seeded.plan_courses,
        plan_reasons=seeded.plan_reasons,
    )
    store.students.save_profile(Student(id=store.stranger))
    store.students.add_plan_set(rows)
    store.students.add_plan_set(rows)  # as a retry would
    current = store.students.current_plan_set(store.stranger)
    assert current.plan_set.complete
    assert [plan.id for plan in current.plans] == [plan.id for plan in rows.plans]
    assert len(store.students.get(store.stranger).plan_sets) == 1


def test_plans_by_id_bring_their_set_and_reasons_and_only_hers(store):
    her = store.mbali
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


def test_her_record_is_her_history_and_six_hearted_electives(store):
    her = store.mbali
    record = store.students.record(her.student.id)
    assert set(record.course_history) == set(her.course_history)
    assert record.favourites == (
        "EEE4114F",
        "EEE4117F",
        "EEE4118F",
        "EEE4119F",
        "EEE4120F",
        "HUB4049F",
    )
    assert store.students.record(store.stranger) == StudentRecord()


def test_hearting_twice_and_unhearting_twice_change_nothing_more(store):
    her = store.mbali.student.id
    for _ in range(2):
        store.students.add_favourite(her, "ECO1006F")
    assert store.students.record(her).favourites.count("ECO1006F") == 1
    for _ in range(2):
        store.students.remove_favourite(her, "ECO1006F")
    assert "ECO1006F" not in store.students.record(her).favourites


def test_hiding_plans_leaves_exactly_the_kept_ones_visible(store):
    # Her seeded set already hides positions 2 to 4, so keeping 2 shows it again, as a retry needs
    her = store.mbali
    plan_set = her.plan_sets[0]
    keep = {plan.id for plan in her.plans if plan.position in (1, 2, 5)}
    store.students.hide_plans(her.student.id, plan_set.id, keep)
    store.students.save_answers(her.student.id, plan_set.id, {"course": "EEE4118F"})
    current = store.students.current_plan_set(her.student.id)
    assert [plan.position for plan in current.plans if not plan.hidden] == [1, 2, 5]
    assert current.plan_set.answers == {"course": "EEE4118F"}


def chat_titled(store: Store, title: str) -> Chat:
    return next(chat for chat in store.mbali.chats if chat.title == title)


def test_her_chats_list_under_exactly_their_plan_or_pair(store):
    her = store.mbali.student.id
    single = chat_titled(store, "Fridays on Power, Control & Robotics")
    pair = chat_titled(store, "Process Control or Medical Imaging")
    alone = store.students.chats(her, single.plan_id, None)
    together = store.students.chats(her, pair.plan_id, pair.other_plan_id)
    assert [chat.id for chat in alone] == [single.id]
    assert [chat.id for chat in together] == [pair.id]
    assert store.students.chat(her, single.id).title == single.title
    assert store.students.chats(store.stranger, single.plan_id, None) == ()
    assert store.students.chat(store.stranger, single.id) is None


def test_a_new_chat_has_its_time_and_lists_first(store):
    her = store.mbali.student.id
    single = chat_titled(store, "Fridays on Power, Control & Robotics")
    new = store.students.add_chat(
        Chat(id=uuid4(), student_id=her, plan_id=single.plan_id)
    )
    assert new.created_at is not None
    newest_first = store.students.chats(her, single.plan_id, None)
    assert [chat.id for chat in newest_first] == [new.id, single.id]


def test_a_chat_reads_back_its_messages_in_order(store):
    her = store.mbali
    pair = chat_titled(store, "Process Control or Medical Imaging")
    question, reply = store.students.messages(her.student.id, pair.id)
    assert (question.message.role, reply.message.role) == ("user", "assistant")
    power_robotics_and_imaging = next(plan for plan in her.plans if plan.position == 7)
    assert reply.message.open_plan_id == power_robotics_and_imaging.id
    assert reply.citations == ()
    assert store.students.messages(store.stranger, pair.id) is None


def test_a_question_and_its_reply_are_stored_together_in_order(store):
    her = store.mbali.student.id
    chat = chat_titled(store, "Fridays on Power, Control & Robotics")
    asked = Message(
        id=uuid4(),
        chat_id=chat.id,
        student_id=her,
        role="user",
        content="Test",
        term="sem1",
    )
    answered = asked.model_copy(
        update={
            "id": uuid4(),
            "role": "assistant",
            "referral": True,
            "open_plan_id": chat.plan_id,
        }
    )
    question, reply = store.students.add_exchange(asked, answered, [])
    assert question.created_at < reply.created_at
    assert (question.model_dump(), reply.model_dump()) == (
        asked.model_dump(),
        answered.model_dump(),
    )
    in_order = [row.message.id for row in store.students.messages(her, chat.id)]
    assert in_order[-2:] == [asked.id, answered.id]


@pytest.mark.integration
def test_a_cited_reply_reads_back_with_its_passage(
    stores, new_account, seed_file, approved_2026
):
    # Supabase only: it joins each citation to its passage, which the fake has no table for. The
    # passage is one the approved 2026 holds, and her account takes the citation with it.
    rules, students = stores
    account = new_account()
    mbali = load_seed(seed_file, account.id)
    seed(rules, students, mbali)
    passage = approved_2026.passages[0]
    chat = mbali.chats[0]
    asked = Message(
        id=uuid4(), chat_id=chat.id, student_id=account.id, role="user", content="Test"
    )
    answered = asked.model_copy(update={"id": uuid4(), "role": "assistant"})
    citation = Citation(
        passage_id=passage.id,
        position=1,
        quote="Test",
        source=passage.source,
        section=passage.section,
        page=passage.page,
    )
    students.add_exchange(asked, answered, [citation])
    reply = students.messages(account.id, chat.id)[-1]
    assert reply.citations == (citation,)


@pytest.mark.integration
def test_a_year_a_plan_uses_is_never_replaced(stores, mbali):
    # Her seeded plans use the approved 2026, so the database refuses to remove that year, and
    # nothing of it changes. sage load --replace goes through this.
    rules, _ = stores
    before = rules.get(2026)
    with pytest.raises(YearInUse):
        rules.replace_year(
            RuleSet(handbook_versions=(HandbookVersion(year=2026, approved=True),))
        )
    assert rules.get(2026) == before
