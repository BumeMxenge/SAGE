# Checks find_plan's contract, which the engine will serve, on Mbali's ten seeded plans. Each
# expected answer is read off data/synthetic/mbali.json by hand, never taken from the code.
import pytest

from evidence import find_plan


@pytest.mark.parametrize(
    ("have", "avoid", "plans"),
    [
        # Only V01 takes all three of EEE4117F, EEE4118F and EEE4119F
        (["EEE4117F", "EEE4118F", "EEE4119F"], [], ["V01"]),
        # The plans without EEE4119F are V02, V03 and V04
        ([], ["EEE4119F"], ["V02", "V03", "V04"]),
        # EEE4118F is in V01 to V04 and V08 to V10, and V03 and V09 also take EEE4120F
        (["EEE4118F"], ["EEE4120F"], ["V01", "V02", "V04", "V08", "V10"]),
    ],
)
def test_a_plan_has_every_course_to_have_and_none_to_avoid(have, avoid, plans):
    assert [plan["plan"] for plan in find_plan(have, avoid)["plans"]] == plans


def test_no_plan_matching_gives_the_sets_reasons():
    # The three further electives leave no room for two of EEE4117F, EEE4118F and EEE4119F
    found = find_plan(["EEE4114F", "EEE4120F", "HUB4049F"], [])
    assert found["plans"] == []
    assert any("at least two of EEE4117F" in reason for reason in found["reasons"])
