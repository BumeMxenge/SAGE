# Checks what Luna is given on Mbali's seed and the approved 2026: her slice holds exactly the
# passages chosen by key, each tool answers from her plans, her record and print as E4's did, a
# missing term on screen says so, a complementary slot's fitting courses reach her message with
# their marks, a pair names each plan on its own reasons, and a course's meetings and a plan's week
# are worded as the plan view shows them
from datetime import time
from uuid import UUID, uuid4

from sage.advisor.evidence import Evidence, meeting_words, week_words
from sage.engine.eligibility import EntryRuleEligibility
from sage.shared.rulebook import Rulebook
from sage.shared.rules import RuleSet, TimetableSlot
from sage.shared.students import PlanCourse, PlanReason
from tests.unit.accounts import MBALI


def test_the_slice_holds_her_plan_courses_and_favourites_and_no_other_course(
    stores, evidence
):
    # She hearts EEE4121F, which is in none of her plans. Its entry joins her slice beside EEE4113F's,
    # a course in every plan, while EEE4126F, in no plan and not hearted, stays out (2026, pp. 138
    # to 141).
    stores[1].add_favourite(MBALI, "EEE4121F")
    sections = {
        (passage.section, passage.page) for passage in evidence().passages.values()
    }
    assert ("EEE4113F Engineering System Design", 138) in sections
    assert ("EEE4121F Mobile and Wireless Networks", 140) in sections
    assert ("EEE4126F Energy Systems & Grids II", 141) not in sections


def test_find_plan_finds_her_hidden_plans_and_else_gives_the_sets_reasons(evidence):
    found = evidence()
    # Her plans with EEE4118F and without EEE4119F are V02 to V04, which her questionnaire answers
    # hide, as data/synthetic/mbali.json gives them
    swapped = found.find_plan(have=["EEE4118F"], avoid=["EEE4119F"])
    assert [
        (plan["plan"], plan["name"], plan["hidden"]) for plan in swapped["plans"]
    ] == [
        ("V02", "Signals, Power & Control", True),
        ("V03", "Power, Control & Embedded", True),
        ("V04", "Power, Control & Imaging", True),
    ]
    # No plan takes three electives outside EEE4117F, EEE4118F and EEE4119F, so it gives the set's
    # five reasons from her seed, and not V07's own
    # A plan asked for by every one of its courses, in any case, is found, and an empty ask isn't one
    v01 = ["CML4607F", "EEE4022S", "EEE4113F", "EEE4117F", "EEE4118F", "EEE4119F"]
    v01 += ["EEE4124C", "EEE4125C"]
    whole = found.find_plan(have=[f" {code.lower()} " for code in v01], avoid=[])
    assert whole == {
        "plans": [
            {
                "plan": "V01",
                "name": "Power, Control & Robotics",
                "hidden": False,
                "courses": v01,
            }
        ]
    }
    assert found.find_plan(have=[], avoid=[]) == {
        "error": "Name at least one course to have or to avoid."
    }
    none = found.find_plan(have=["EEE4114F", "EEE4120F", "HUB4049F"], avoid=[])
    assert none["plans"] == []
    assert sorted(none["reasons"]) == sorted(
        [
            (
                "Every plan includes the five core courses: EEE4113F, CML4607F, EEE4124C, "
                "EEE4125C and EEE4022S."
            ),
            (
                "Every plan takes at least two of EEE4117F, EEE4118F and EEE4119F, and 48 "
                "elective credits in all, which makes 138 credits for the year."
            ),
            (
                "EEE4022S needs a pass in one of the fourth-year electives. Every plan takes "
                "at least two of them in the first semester."
            ),
            (
                "Plans with a fourth elective aren't listed. The handbook allows more than 48 "
                "elective credits, so ask your advisor if you want to add one."
            ),
            (
                "Your record shows Practical Training (EEE1000X and EEE3000X) still in "
                "progress. Both are needed to graduate, so check with your advisor when they "
                "will be signed off."
            ),
        ]
    )


def test_get_course_gives_what_e4_gave(evidence, e4):
    # E4's get_course, on the same approved 2026, for a course, the same in any case and spacing,
    # and a code the year doesn't print
    found = evidence()
    for code in ("EEE4118F", " eee4118f ", "ABC1234F"):
        assert found.get_course(code) == e4.get_course(code)


def test_check_eligibility_asks_the_engine_about_her_record(evidence):
    found = evidence()
    # Her record shows EEE3096S Embedded Systems II passed in 2025 with 80%, and EEE4118F Process
    # Control and Instrumentation is in her plans, so she may take it
    assert found.run("check_eligibility", {"code": "EEE3096S"}) == {
        "status": "not_eligible",
        "reason": "You've already passed EEE3096S.",
    }
    assert found.run("check_eligibility", {"code": " eee4118f "}) == {
        "status": "eligible",
        "reason": None,
    }
    assert found.run("check_eligibility", {"code": "ABC1234F"}) == {
        "error": "No course ABC1234F in the 2026 handbook."
    }


def test_a_question_with_no_term_on_screen_says_so(stores, chat_on):
    rules, students = stores
    found = Evidence(
        chat_on(1), None, students, Rulebook(rules), EntryRuleEligibility()
    )
    assert "- Term on screen: none" in found.context().splitlines()


def add_slot_reason(students, position: int) -> PlanReason:
    # A made-up complementary slot on her plan at this position, in the engine's shape, with four
    # approved courses that fit: one plain, one with a meeting at no printed time, one worth fewer
    # than the line's 18 credits and one both
    state = students.get(MBALI)
    plan = next(plan for plan in state.plans if plan.position == position)
    slot = PlanReason(
        id=uuid4(),
        plan_set_id=plan.plan_set_id,
        student_id=MBALI,
        plan_id=plan.id,
        kind="included",
        message="Add one approved complementary studies course: 4 fit this plan's timetable.",
        details={
            "credits": 18,
            "fits": ["EGS1007S", "BIO1004S", "PHI1010S", "REL1006S"],
            "untimed": ["BIO1004S", "REL1006S"],
            "fewer_credits": ["PHI1010S", "REL1006S"],
            "sections": {},
            "forced": {},
        },
    )
    students.replace(
        state.model_copy(update={"plan_reasons": (*state.plan_reasons, slot)})
    )
    return slot


def test_a_slots_fitting_courses_reach_her_message_with_their_marks(stores, evidence):
    # Each goes under the slot by the code and name the approved 2026 complementary workbook gives it
    slot = add_slot_reason(stores[1], 1)
    lines = evidence().context().splitlines()
    under = lines.index(f"- {slot.message}") + 1
    assert lines[under : under + 4] == [
        "  - EGS1007S Human & Physical Systems",
        "  - BIO1004S Biological Diversity: a meeting with no printed time",
        "  - PHI1010S Ethics: worth fewer than 18 credits",
        (
            "  - REL1006S Judaism, Christianity and Islam: a meeting with no printed time, "
            "worth fewer than 18 credits"
        ),
    ]


def test_in_a_pair_each_plans_own_reasons_carry_its_name(stores, chat_on):
    # Her seed gives V07 Power, Robotics & Imaging a reason of its own, about its Thursdays, and her
    # set reasons that cover every plan (data/synthetic/mbali.json). A slot on V01 Power, Control &
    # Robotics keeps its courses under its named line. Alone on V07, its "this plan" is the open one.
    rules, students = stores
    slot = add_slot_reason(students, 1)
    own = "In semester 1 this plan has one class on Thursdays: CML4607F at 12:00."
    every = (
        "Every plan includes the five core courses: EEE4113F, CML4607F, EEE4124C, "
        "EEE4125C and EEE4022S."
    )

    def reasons(*positions: int) -> list[str]:
        found = Evidence(
            chat_on(*positions),
            "sem1",
            students,
            Rulebook(rules),
            EntryRuleEligibility(),
        )
        return found.context().split("Reasons behind the plan set\n")[1].splitlines()

    pair = reasons(1, 7)
    assert {f"- V07 Power, Robotics & Imaging: {own}", f"- {every}"} <= set(pair)
    named = pair.index(f"- V01 Power, Control & Robotics: {slot.message}")
    assert pair[named + 1] == "  - EGS1007S Human & Physical Systems"
    assert f"- {own}" in reasons(7)


def slot(
    day: int | None,
    hours: tuple[int, int] | None,
    course: str = "TST4000F",
    term: str = "sem1",
    **fields,
) -> TimetableSlot:
    # One meeting of a made-up course, starting and ending on the hour
    start, end = hours or (None, None)
    return TimetableSlot(
        id=uuid4(),
        handbook_year=2026,
        course_code=course,
        term=term,
        day=day,
        start_time=time(start) if start is not None else None,
        end_time=time(end) if end is not None else None,
        **fields,
    )


def test_meetings_are_worded_as_the_plan_view_shows_them():
    rules = RuleSet(
        timetable_slots=(
            slot(1, (8, 10), kind="lecture"),
            slot(2, None, kind="tutorial"),
            slot(None, (12, 13)),
            slot(None, None, kind="screening"),
            slot(1, (14, 17), kind="practical", choice_group="practical", choice="A"),
            slot(2, (14, 17), kind="practical", choice_group="practical", choice="B"),
            # One alternative that meets twice, as CSC3002F's pairs of days do
            *(
                slot(
                    day, (14, 18), kind="lab", choice_group="lab", choice="Wed and Thu"
                )
                for day in (3, 4)
            ),
            slot(5, (14, 18), kind="lab", choice_group="lab", choice="Fri"),
        )
    )

    def course(choices: dict[str, list[str]] | None) -> PlanCourse:
        return PlanCourse(
            plan_id=uuid4(),
            course_code="TST4000F",
            student_id=UUID(int=1),
            handbook_year=2026,
            choices=choices,
        )

    # With nothing chosen, every alternative is one of several
    assert meeting_words(course(None), rules, "EB011EEE05") == (
        "Meets Mon 08:00 to 10:00 (lecture), Tue, at no printed time (tutorial), "
        "12:00 to 13:00, on no printed day, at no printed day or time (screening). "
        "Attends one practical: A (Mon 14:00 to 17:00) or B (Tue 14:00 to 17:00). "
        "Attends one lab: Wed and Thu (Wed 14:00 to 18:00, Thu 14:00 to 18:00) or Fri "
        "(Fri 14:00 to 18:00)."
    )
    # With one practical left, it's one she attends, in its place in the week
    assert meeting_words(course({"practical": ["B"]}), rules, "EB011EEE05") == (
        "Meets Mon 08:00 to 10:00 (lecture), Tue 14:00 to 17:00 (practical), "
        "Tue, at no printed time (tutorial), 12:00 to 13:00, on no printed day, "
        "at no printed day or time (screening). "
        "Attends one lab: Wed and Thu (Wed 14:00 to 18:00, Thu 14:00 to 18:00) or Fri "
        "(Fri 14:00 to 18:00)."
    )


def test_a_plans_week_lists_each_days_meetings_in_time_order():
    # Made-up courses of every term, given out of time order. Worked out by hand: a quarter shows in
    # its semester with its mark, a full-year course in both semesters, winter and summer in weeks of
    # their own and "other" in none. A meeting with a day but no time ends its day, one with no day
    # follows the days, and each lab alternative is one of two until one is chosen.
    rules = RuleSet(
        timetable_slots=(
            slot(1, (9, 10), "EEE1000S", "sem2"),
            slot(2, None, "EEE1000S", "sem2", kind="tutorial"),
            slot(None, (12, 13), "EEE1000S", "sem2", kind="screening"),
            slot(2, (14, 15), "DDD1000C", "q3", kind="lecture"),
            slot(2, (14, 15), "DDD1000D", "q4"),
            slot(2, (8, 9), "BBB1000H", "full_year"),
            slot(1, (8, 9), "AAA1000F", kind="lecture"),
            slot(3, (10, 11), "AAA1000F", kind="lecture"),
            slot(5, (14, 17), "AAA1000F", kind="lab", choice_group="lab", choice="A"),
            slot(4, (14, 17), "AAA1000F", kind="lab", choice_group="lab", choice="B"),
            slot(1, (12, 13), "CCC1000A", "q1"),
            slot(1, (12, 13), "CCC1000B", "q2"),
            slot(3, (9, 10), "FFF1000L", "winter"),
            slot(4, (9, 10), "GGG1000U", "summer"),
            slot(5, (9, 10), "HHH1000X", "other"),
        )
    )
    codes = ["EEE1000S", "DDD1000C", "DDD1000D", "BBB1000H", "AAA1000F"]
    codes += ["CCC1000A", "CCC1000B", "FFF1000L", "GGG1000U", "HHH1000X"]
    plan_id = uuid4()

    def plan(lab: list[str] | None) -> list[PlanCourse]:
        return [
            PlanCourse(
                plan_id=plan_id,
                course_code=code,
                student_id=UUID(int=1),
                handbook_year=2026,
                choices={"lab": lab} if lab and code == "AAA1000F" else None,
            )
            for code in codes
        ]

    assert week_words(plan(None), rules, "EB011EEE05") == [
        "Week in sem1, day by day",
        (
            "- Mon: AAA1000F 08:00 to 09:00 (lecture), CCC1000A 12:00 to 13:00 (Q1), "
            "CCC1000B 12:00 to 13:00 (Q2)"
        ),
        "- Tue: BBB1000H 08:00 to 09:00",
        "- Wed: AAA1000F 10:00 to 11:00 (lecture)",
        "- Thu: AAA1000F 14:00 to 17:00 (one of 2 lab choices: B)",
        "- Fri: AAA1000F 14:00 to 17:00 (one of 2 lab choices: A)",
        "Week in sem2, day by day",
        "- Mon: EEE1000S 09:00 to 10:00",
        (
            "- Tue: BBB1000H 08:00 to 09:00, DDD1000C 14:00 to 15:00 (lecture, Q3), "
            "DDD1000D 14:00 to 15:00 (Q4), EEE1000S at no printed time (tutorial)"
        ),
        "- No printed day: EEE1000S 12:00 to 13:00 (screening)",
        "Week in winter, day by day",
        "- Wed: FFF1000L 09:00 to 10:00",
        "Week in summer, day by day",
        "- Thu: GGG1000U 09:00 to 10:00",
    ]
    # With lab A chosen, it's a lab she attends, and her Thursday is free
    assert week_words(plan(["A"]), rules, "EB011EEE05")[3:5] == [
        "- Wed: AAA1000F 10:00 to 11:00 (lecture)",
        "- Fri: AAA1000F 14:00 to 17:00 (lab)",
    ]
