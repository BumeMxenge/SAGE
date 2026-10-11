# Checks the questionnaire on Mbali's plan set, made fresh again: the questions it builds reproduce the
# prototype's, answers hide exactly the plans they don't keep, and it can only be answered once
import pytest

from tests.unit.api.accounts import MBALI


@pytest.fixture
def mbali(signed_in, stores):
    # Her seeded set as it was before she answered: nothing hidden and no answers
    students = stores[1]
    state = students.get(MBALI)
    students.replace(
        state.model_copy(
            update={
                "plan_sets": tuple(
                    row.model_copy(update={"answers": None}) for row in state.plan_sets
                ),
                "plans": tuple(
                    plan.model_copy(update={"hidden": False}) for plan in state.plans
                ),
            }
        )
    )
    return signed_in("mbali")


@pytest.fixture
def positions(mbali) -> dict[str, int]:
    # Plan positions by id, to read options' keeps as positions
    return {
        plan["id"]: plan["position"] for plan in mbali.get("/v1/plans").json()["plans"]
    }


def options(mbali, question: str) -> dict[str, dict]:
    questionnaire = mbali.get("/v1/questionnaire").json()
    (found,) = [q for q in questionnaire["questions"] if q["id"] == question]
    return {option["id"]: option for option in found["options"]}


def kept(option, positions) -> list[int]:
    return sorted(positions[plan_id] for plan_id in option["keeps"])


def visible(plan_set) -> list[int]:
    return [plan["position"] for plan in plan_set["plans"] if not plan["hidden"]]


def test_a_fresh_set_needs_it(mbali):
    assert mbali.get("/v1/plans").json()["questionnaire_needed"] is True
    assert mbali.get("/v1/questionnaire").json()["needed"] is True


def test_the_course_options_are_her_hearted_electives(mbali):
    course = options(mbali, "course")
    assert list(course) == [
        "EEE4114F",
        "EEE4117F",
        "EEE4118F",
        "EEE4119F",
        "EEE4120F",
        "HUB4049F",
        "no_preference",
    ]
    assert all(
        option["hearted"] for code, option in course.items() if code != "no_preference"
    )
    assert (
        course["EEE4119F"]["label"] == "MECHATRONICS"
    )  # the name as the handbook prints it


def test_each_option_keeps_the_prototypes_plans(mbali, positions):
    course, week = options(mbali, "course"), options(mbali, "week")
    assert kept(course["EEE4119F"], positions) == [1, 5, 6, 7, 8, 9, 10]
    assert kept(week["fewest_8am"], positions) == [8, 9, 10]
    assert kept(week["lunch_free"], positions) == [1, 2, 3, 5, 6, 8, 9]
    assert kept(course["no_preference"], positions) == list(range(1, 11))
    assert kept(week["no_preference"], positions) == list(range(1, 11))


def test_answering_hides_every_plan_the_answers_dont_keep(mbali):
    response = mbali.post(
        "/v1/questionnaire", json={"course": "EEE4118F", "week": "lunch_free"}
    )
    assert response.status_code == 200
    plan_set = response.json()
    assert visible(plan_set) == [1, 2, 3, 8, 9]
    assert plan_set["questionnaire_needed"] is False


def test_answers_that_keep_nothing_are_refused(mbali):
    response = mbali.post(
        "/v1/questionnaire", json={"course": "HUB4049F", "week": "lunch_free"}
    )
    assert (response.status_code, response.json()["code"]) == (422, "no_plan_matches")
    assert visible(mbali.get("/v1/plans").json()) == list(
        range(1, 11)
    )  # nothing hidden


def test_an_answer_that_isnt_an_option_is_refused(mbali):
    response = mbali.post(
        "/v1/questionnaire", json={"course": "CML4607F"}
    )  # in every plan
    assert (response.status_code, response.json()["code"]) == (422, "unknown_answer")


def test_a_retry_after_a_failed_save_shows_exactly_what_its_answers_keep(
    mbali, stores, monkeypatch
):
    # The first attempt hides the plans HUB4049F doesn't keep, then fails before storing its
    # answers, so the questionnaire stays open for another answer
    def outage(*args):
        raise ConnectionError("made-up outage")

    monkeypatch.setattr(stores[1], "save_answers", outage)
    failed = mbali.post("/v1/questionnaire", json={"course": "HUB4049F"})
    assert failed.status_code == 500
    monkeypatch.undo()
    response = mbali.post("/v1/questionnaire", json={"course": "EEE4118F"})
    assert response.status_code == 200
    assert visible(response.json()) == [1, 2, 3, 4, 8, 9, 10]


def test_it_can_only_be_answered_once(mbali):
    assert (
        mbali.post("/v1/questionnaire", json={"course": "EEE4119F"}).status_code == 200
    )
    response = mbali.post("/v1/questionnaire", json={"course": "EEE4118F"})
    assert (response.status_code, response.json()["code"]) == (
        409,
        "questionnaire_answered",
    )


def test_her_seeded_answered_set_doesnt_need_it(signed_in):
    mbali = signed_in("mbali")  # her set as seeded, already answered
    assert mbali.get("/v1/questionnaire").json() == {"needed": False, "questions": []}
    response = mbali.post("/v1/questionnaire", json={"course": "EEE4119F"})
    assert (response.status_code, response.json()["code"]) == (
        409,
        "questionnaire_answered",
    )


def test_a_set_of_5_plans_doesnt_need_it(mbali, stores):
    students = stores[1]
    state = students.get(MBALI)
    first_five = tuple(plan for plan in state.plans if plan.position <= 5)
    ids = {plan.id for plan in first_five}
    students.replace(
        state.model_copy(
            update={
                "plans": first_five,
                "plan_courses": tuple(
                    row for row in state.plan_courses if row.plan_id in ids
                ),
                "plan_reasons": tuple(
                    row for row in state.plan_reasons if row.plan_id in ids | {None}
                ),
                "chats": (),
                "messages": (),
            }
        )
    )
    assert mbali.get("/v1/questionnaire").json()["needed"] is False
    response = mbali.post("/v1/questionnaire", json={})
    assert (response.status_code, response.json()["code"]) == (
        409,
        "questionnaire_not_needed",
    )
