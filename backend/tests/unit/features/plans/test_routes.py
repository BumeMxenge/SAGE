# Checks the planner's plan reads on Mbali's seeded set: what the set shows, each plan in full, and a
# comparison, which needs both plans to be hers. Her other plans and chats are guarded in
# test_guards.py.
from tests.unit.accounts import MBALI


def test_her_set_has_10_plans_and_7_still_visible(mbali):
    plan_set = mbali.get("/v1/plans").json()
    assert (plan_set["period"], plan_set["version"]) == (2026, 1)
    assert plan_set["questionnaire_needed"] is False  # her seeded set is answered
    positions = [plan["position"] for plan in plan_set["plans"]]
    assert positions == list(range(1, 11))
    visible = [plan["position"] for plan in plan_set["plans"] if not plan["hidden"]]
    assert visible == [1, 5, 6, 7, 8, 9, 10]
    # p. 58's fourth-year total: the five core courses' 90 credits and three 16-credit electives
    assert {plan["credits"] for plan in plan_set["plans"]} == {138}
    # The set's own reasons: the seed's six, less the one for plan 7 alone
    assert len(plan_set["reasons"]) == 5


def test_a_plan_is_named_over_its_combination(mbali, plan_ids):
    # Plan 1's electives are the prototype's "EEE4117F · EEE4118F · EEE4119F", one theme word each
    named = ("Power, Control & Robotics", "EEE4117F · EEE4118F · EEE4119F")
    summary = mbali.get("/v1/plans").json()["plans"][0]
    plan = mbali.get(f"/v1/plans/{plan_ids[1]}").json()
    assert (summary["name"], summary["combination"]) == named
    assert (plan["name"], plan["combination"]) == named


def test_every_plan_has_138_credits_split_by_term(mbali, plan_ids):
    # From the entries (pp. 138 to 141, 162 and 164): semester 1 holds EEE4113F's 16, CML4607F's 10
    # and the three electives' 48; the third quarter EEE4124C's 8 and EEE4125C's 16; semester 2
    # EEE4022S's 40
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
    # The labels p. 58 prints over her fourth-year tables, and EEE4117F's 8am lectures on the EB011
    # sheet (C53:C54, E53:E54 and G53). The sheet prints no meeting for EEE4022S.
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


def test_her_plan_shows_the_meetings_only_her_curriculum_has(mbali, plan_ids):
    # EEE4120F's Thursday 16:00 meeting is printed on her EB011 sheet (F61:F62) but not on EB022's,
    # so it's linked to the Mechatronics curricula, and plan 3 shows it as the route hands the filter
    # her curriculum. The filter itself is tested in tests/unit/features/plans/test_service.py.
    courses = {
        course["code"]: course
        for course in mbali.get(f"/v1/plans/{plan_ids[3]}").json()["courses"]
    }
    meetings = [(m["day"], m["start_time"]) for m in courses["EEE4120F"]["meetings"]]
    assert (4, "16:00:00") in meetings


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
