# Checks that my theme words cover every elective the approved 2026 lists
from sage.engine.generator import groups
from sage.engine.themes import WORDS
from sage.shared.rules import COMPLEMENTARY, ChooseFromGroup, CreditsFromGroups


def test_every_course_in_a_2026_choose_or_credits_group_has_a_word(approved_2026):
    # The approved complementary courses fill a plan's slots rather than name it, so need none
    named = {
        group
        for rule in approved_2026.curriculum_rules
        for part in rule.rule.all
        if isinstance(part, ChooseFromGroup | CreditsFromGroups)
        for group in groups(part)
        if group != COMPLEMENTARY
    }
    electives = {
        member.course_code
        for member in approved_2026.course_group_members
        if member.group_key in named
    }
    assert electives  # the groups were found
    assert electives - WORDS.keys() == set()
