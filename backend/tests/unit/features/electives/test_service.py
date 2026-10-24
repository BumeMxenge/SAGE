# Checks Explore Electives' cards on made-up rules: one card per course, on its first offering's tab,
# and which offerings she can heart, with the card's one note, worked out by hand from the rule in
# service.py. Each slot is a complementary slot's details as the engine writes them, on an 18-credit
# line, and each plan has its own.
import pytest

from sage.features.electives.service import NO_FIT, UNTIMED, cards
from sage.shared.planning import Eligibility
from sage.shared.rules import Course, CourseGroupMember, RuleSet


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
ELIGIBLE = Eligibility(status="eligible")
PERMISSION = "It needs permission of the convener, which only your advisor can judge."
NEEDS = "It needs HST1012F, which your record doesn't show yet."
FEWER = (
    "It's worth fewer than your plans' 18-credit complementary line, so check it with your "
    "advisor."
)


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
        (
            (F, S),
            [slot("HST1013F")],
            {},
            "Only the semester 1 offering fits your plans.",
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
    ((_, (card,)),) = cards(rules, eligibility, ("HST1013S",), [slot("HST1013F")])
    # The check outranks the second offering not fitting, and the card shows her heart on it
    assert (card.note, [o.works for o in card.offerings], card.hearted) == (
        PERMISSION,
        [True, False],
        True,
    )
