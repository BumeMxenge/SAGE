# Checks Explore Electives' cards on made-up rules: one card per course, on its first offering's tab,
# and which offerings she can heart, with the card's one note, worked out by hand from the rule in
# service.py. Each slot is a complementary slot's details as the engine writes them, on an 18-credit
# line, and each plan has its own. Then that the page reads the slots of her current plan set, on
# Mbali's seed.
from uuid import uuid4

import pytest

from sage.features.electives.service import by_tab, cards
from sage.shared.planning import Eligibility
from sage.shared.rulebook import Rulebook
from sage.shared.rules import Course, CourseGroupMember, RuleSet
from sage.shared.students import PlanReason, PlanSet, PlanSetRows
from tests.unit.accounts import MBALI


def course(code, term, credits=18):
    return Course(
        handbook_year=2026,
        code=code,
        name="Made Up History",
        credits=credits,
        nqf_level=5,
        term=term,
    )


def member(code, tab="history"):
    return CourseGroupMember(
        handbook_year=2026, group_key="complementary", course_code=code, category=tab
    )


def slot(*fits, untimed=(), fewer=()):
    return {
        "credits": 18,
        "fits": list(fits),
        "untimed": list(untimed),
        "fewer_credits": list(fewer),
        "sections": {},
        "forced": {},
    }


F, S = course("HST1013F", "sem1"), course("HST1013S", "sem2")
WINTER = course("HST1013L", "winter")
ELIGIBLE = Eligibility(status="eligible")
PERMISSION = "It needs permission of the convener, which only your advisor can judge."
NEEDS = "It needs HST1012F, which your record doesn't show yet."
# The note's words, as I gave them
NO_FIT = "Doesn't fit your plans' timetables."
ONLY_F = "Only the semester 1 offering fits your plans."
UNTIMED = "One of its classes has no set day or time, so check with your advisor."
FEWER = "It's worth fewer credits than your complementary course needs, so check with your advisor."


def test_one_card_per_course_on_its_first_offerings_tab():
    # HST1013S is on another tab from HST1013F, and HST1015S is worth other credits from HST1015F,
    # so it's another course
    offered = (F, S, course("HST1015F", "sem1"), course("HST1015S", "sem2", 36))
    rules = RuleSet(
        courses=offered,
        course_group_members=(
            member("HST1013F"),
            member("HST1013S", "society"),
            member("HST1015F"),
            member("HST1015S", "society"),
        ),
    )
    found = cards(rules, {c.code: ELIGIBLE for c in offered}, (), ())
    assert [
        (tab, [[o.course.code for o in card.offerings] for card in tab_cards])
        for tab, tab_cards in found
    ] == [
        ("history", [["HST1013F", "HST1013S"], ["HST1015F"]]),
        ("society", [["HST1015S"]]),
    ]


@pytest.mark.parametrize(
    ("offered", "slots", "refused", "note", "works"),
    [
        # Each offering fits one plan's slot, and the engine passes both
        ((F, S), [slot("HST1013F"), slot("HST1013S")], {}, None, [True, True]),
        # No plan has a complementary slot, so only eligibility counts
        ((F, S), [], {}, None, [True, True]),
        # Only the first semester's offering fits
        ((F, S), [slot("HST1013F")], {}, ONLY_F, [True, False]),
        # Only the first semester's offering fits, and it needs a check, which the note adds
        (
            (F, S),
            [slot("HST1013F", untimed=["HST1013F"])],
            {},
            f"{ONLY_F} {UNTIMED}",
            [True, False],
        ),
        # Both fit, but the engine refuses the second, so its reason is the note
        (
            (F, S),
            [slot("HST1013F", "HST1013S")],
            {"HST1013S": NEEDS},
            NEEDS,
            [True, False],
        ),
        # Neither fits any plan
        ((F, S), [slot("ECO1010F")], {}, NO_FIT, [False, False]),
        # The engine refuses both, which its reason says before the timetable
        (
            (F, S),
            [slot("ECO1010F")],
            {"HST1013F": NEEDS, "HST1013S": NEEDS},
            NEEDS,
            [False, False],
        ),
        # A course offered once that fits no plan
        ((F,), [slot("ECO1010F")], {}, NO_FIT, [False]),
        # A meeting with no printed time keeps the heart, with what to check
        (
            (F, S),
            [slot("HST1013F", "HST1013S", untimed=["HST1013S"])],
            {},
            UNTIMED,
            [True, True],
        ),
        # Both offerings need that check, which the note says once
        (
            (F, S),
            [slot("HST1013F", "HST1013S", untimed=["HST1013F", "HST1013S"])],
            {},
            UNTIMED,
            [True, True],
        ),
        # Three offerings, of which the winter one fits no plan
        (
            (F, WINTER, S),
            [slot("HST1013F", "HST1013S")],
            {},
            "Only the semester 1 and semester 2 offerings fit your plans.",
            [True, False, True],
        ),
        # Fewer credits than the only slot listing it needs
        (
            (F,),
            [slot("HST1013F", fewer=["HST1013F"])],
            {},
            FEWER,
            [True],
        ),
        # Fewer than one slot needs, but enough for another plan's, so nothing to check
        (
            (F,),
            [slot("HST1013F", fewer=["HST1013F"]), slot("HST1013F")],
            {},
            None,
            [True],
        ),
    ],
)
def test_an_offering_works_when_the_engine_allows_it_and_it_fits_a_plan(
    offered, slots, refused, note, works
):
    eligibility = {c.code: ELIGIBLE for c in offered} | {
        code: Eligibility(status="not_eligible", reason=reason)
        for code, reason in refused.items()
    }
    rules = RuleSet(
        courses=offered, course_group_members=tuple(member(c.code) for c in offered)
    )
    ((_, (card,)),) = cards(rules, eligibility, (), slots)
    assert (card.note, [o.works for o in card.offerings], card.can_heart) == (
        note,
        works,
        any(works),
    )


def test_a_check_verdict_keeps_the_heart_with_its_reason():
    eligibility = {
        "HST1013F": Eligibility(status="check", reason=PERMISSION),
        "HST1013S": ELIGIBLE,
    }
    rules = RuleSet(
        courses=(F, S), course_group_members=(member(F.code), member(S.code))
    )
    slots = [slot("HST1013F", "HST1013S")]
    ((_, (card,)),) = cards(rules, eligibility, ("HST1013S",), slots)
    # Both still work, and the card shows her heart on the second
    assert (card.note, [o.works for o in card.offerings], card.hearted) == (
        PERMISSION,
        [True, True],
        True,
    )


class Eligible:
    # Finds every course eligible, so only her plans decide what works
    def check(self, courses, history, rules, symbols, student):
        return {course.code: ELIGIBLE for course in courses}


def test_the_slots_of_her_current_plan_set_decide_what_works(stores):
    # Mbali's seeded set has no complementary slot, so Greek IA and Latin IA both work. A later set
    # whose slot lists Greek IA alone leaves Latin IA out.
    rules, students = stores
    rulebook, student = Rulebook(rules), students.profile(MBALI)

    def works():
        found = by_tab(students, rulebook, Eligible(), student)
        codes = {
            o.course.code: o.works
            for _, tab in found
            for card in tab
            for o in card.offerings
        }
        return codes["SLL1052F"], codes["SLL1050F"]

    assert works() == (True, True)
    later = PlanSet(id=uuid4(), student_id=MBALI, period=2026, version=2)
    reason = PlanReason(
        id=uuid4(),
        plan_set_id=later.id,
        student_id=MBALI,
        kind="included",
        message="One complementary course fits.",
        details=slot("SLL1052F"),
    )
    students.add_plan_set(PlanSetRows(plan_set=later, plan_reasons=(reason,)))
    assert works() == (True, False)
