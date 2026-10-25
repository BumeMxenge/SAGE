# Checks how a slot's courses are counted, on made-up offerings: a course's offerings join as
# Explore Electives' cards join them, and a course needs a check when one of its fitting offerings
# does
from uuid import UUID

from sage.shared.slots import PlanSlot, course_counts

CREDITS = {
    "HST1013F": 18,
    "HST1013S": 18,
    "ECO1010F": 18,
    "ECO1010S": 18,
    "HST1015F": 18,
    "HST1015S": 36,
    "PHI1010S": 15,
}


def test_a_course_counts_once_and_needs_a_check_when_either_offering_does():
    # Seven offerings are five courses: HST1013 and ECO1010 are offered twice, and HST1015S, at 36
    # credits, isn't HST1015F's. Three need a check: HST1013, both offerings untimed, ECO1010, its
    # second offering untimed, and PHI1010S, at 15 credits under the line's 18.
    slot = PlanSlot(
        plan_id=UUID(int=1),
        message="Made up.",
        credits=18,
        fits=tuple(CREDITS),
        untimed=("HST1013F", "HST1013S", "ECO1010S"),
        fewer_credits=("PHI1010S",),
        sections={},
        forced={},
    )
    assert course_counts(slot, CREDITS) == (5, 3)
