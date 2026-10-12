# Checks the planner's plan reads on Mbali's seeded set: what the set shows, each plan in full, and a
# comparison, which needs both plans to be hers. Her other plans and chats are guarded in
# test_guards.py.
from tests.unit.api.accounts import MBALI


def test_her_set_has_10_plans_and_7_still_visible(mbali):
    plan_set = mbali.get("/v1/plans").json()
    assert (plan_set["period"], plan_set["version"]) == (2026, 1)
    assert plan_set["questionnaire_needed"] is False  # her seeded set is answered
    positions = [plan["position"] for plan in plan_set["plans"]]
    assert positions == list(range(1, 11))
    visible = [plan["position"] for plan in plan_set["plans"] if not plan["hidden"]]
    assert visible == [1, 5, 6, 7, 8, 9, 10]
    assert {plan["credits"] for plan in plan_set["plans"]} == {138}
    # The set's own reasons: the seed's six, less the one for plan 7 alone
    assert len(plan_set["reasons"]) == 5


def test_every_plan_has_138_credits_split_by_term(mbali, plan_ids):
    for plan_id in plan_ids.values():
        credits = mbali.get(f"/v1/plans/{plan_id}").json()["credits"]
        assert credits == {"total": 138, "by_term": {"sem1": 74, "q3": 24, "sem2": 40}}


def test_position_7_adds_one_reason_of_its_own(mbali, plan_ids):
    reasons = mbali.get(f"/v1/plans/{plan_ids[7]}").json()["reasons"]
    assert len(reasons) == 6
    assert reasons[-1]["message"].startswith(
        "In semester 1 this plan has one class on Thursdays"
    )


def test_a_plan_shows_each_courses_groups_and_meetings(mbali, plan_ids):
    courses = {
        course["code"]: course
        for course in mbali.get(f"/v1/plans/{plan_ids[1]}").json()["courses"]
    }
    assert [group["label"] for group in courses["EEE4119F"]["groups"]] == [
        "Fourth Year Elective Core Courses (ME)"
    ]
    assert [group["label"] for group in courses["CML4607F"]["groups"]] == [
        "Fourth Year Core Courses (ME)"
    ]
    eight_oclocks = [
        (meeting["day"], meeting["start_time"])
        for meeting in courses["EEE4117F"]["meetings"]
    ]
    assert eight_oclocks == [(1, "08:00:00"), (3, "08:00:00"), (5, "08:00:00")]
    assert courses["EEE4022S"]["meetings"] == []  # no contact time


def test_a_hidden_plan_still_opens(mbali, plan_ids):
    response = mbali.get(f"/v1/plans/{plan_ids[2]}")
    assert response.status_code == 200
    assert response.json()["hidden"] is True


def test_comparing_1_and_7(mbali, plan_ids):
    comparison = mbali.get(
        "/v1/plans/compare", params={"first": plan_ids[1], "second": plan_ids[7]}
    ).json()
    assert len(comparison["shared"]) == 7
    assert comparison["only_first"] == ["EEE4118F"]
    assert comparison["only_second"] == ["HUB4049F"]
    assert comparison["first"]["position"] == 1


def test_a_plan_compared_with_itself_is_refused(mbali, plan_ids):
    response = mbali.get(
        "/v1/plans/compare", params={"first": plan_ids[1], "second": plan_ids[1]}
    )
    assert (response.status_code, response.json()["code"]) == (422, "same_plan")


def test_another_students_plan_beside_their_own_is_not_found(signed_in, plan_ids):
    # The sweep sends two of Mbali's plans. One of the student's own beside one of hers must fail too.
    other = signed_in("zvsorw")
    own = other.get("/v1/plans").json()["plans"][0]["id"]
    response = other.get(
        "/v1/plans/compare", params={"first": own, "second": plan_ids[1]}
    )
    assert (response.status_code, response.json()["code"]) == (404, "plan_not_found")


def test_no_complete_set_means_plans_arent_ready(mbali, stores):
    students = stores[1]
    state = students.get(MBALI)
    unfinished = [row.model_copy(update={"complete": False}) for row in state.plan_sets]
    students.replace(state.model_copy(update={"plan_sets": tuple(unfinished)}))
    response = mbali.get("/v1/plans")
    assert (response.status_code, response.json()["code"]) == (409, "plans_not_ready")
